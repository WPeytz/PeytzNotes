"""One-time, reviewable refresh of a Notion Markdown export.

Dry run by default. Use --apply only after reviewing the reported changes.
Existing note IDs and visibility are preserved; missing pages are never deleted.
"""

import argparse
import re
import tempfile
import uuid
import zipfile
from contextlib import closing, contextmanager
from pathlib import Path

from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

from ingestion.notion_parser import ParsedNote, parse_export
from ingestion.chunker import chunk_note
from ingestion.embedder import embed_texts
from ingestion.uploader import get_connection


NOTION_ID = re.compile(r"([a-f0-9]{32})(?:\.md)?$")
def notion_id(path: str) -> str | None:
    match = NOTION_ID.search(path)
    return match.group(1) if match else None


@contextmanager
def export_directory(export: Path):
    if export.is_dir():
        yield export
        return
    if not zipfile.is_zipfile(export):
        raise ValueError("Expected a Notion export directory or ZIP file")

    with tempfile.TemporaryDirectory(prefix="peytznotes-export-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(export) as archive:
            total_bytes = 0
            for item in archive.infolist():
                destination = (root / item.filename).resolve()
                if not destination.is_relative_to(root.resolve()):
                    raise ValueError("Export contains an unsafe file path")
                total_bytes += item.file_size
                if item.file_size > 150 * 1024 * 1024 or total_bytes > 3 * 1024 * 1024 * 1024:
                    raise ValueError("Export is larger than the safe processing limit")
            archive.extractall(root)
        yield root


def find_notes_root(export: Path) -> Path:
    """Find the directory containing the three PeytzNotes collections."""
    candidates = []
    for directory in [export, *export.rglob("*")]:
        if not directory.is_dir():
            continue
        md_names = {item.stem for item in directory.glob("*.md")}
        if any(name.startswith("AI & Data") for name in md_names) and any(
            name.startswith("Human-Centered AI") for name in md_names
        ):
            candidates.append(directory)
    if len(candidates) != 1:
        raise ValueError(f"Could not identify one PeytzNotes export root (found {len(candidates)})")
    return candidates[0]


def read_existing(connection) -> dict[str, dict]:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, course, source_path, raw_content, is_public
            FROM notes WHERE source_path NOT LIKE 'uploads/%'
        """)
        rows = cursor.fetchall()
    by_notion_id = {}
    for row in rows:
        page_id = notion_id(row[3])
        if page_id:
            if page_id in by_notion_id:
                raise ValueError(f"Duplicate Notion page ID in database: {page_id}")
            by_notion_id[page_id] = dict(zip(
                ("id", "title", "course", "source_path", "content", "is_public"), row
            ))
    return by_notion_id


def changes_for(notes: list[ParsedNote], existing: dict[str, dict]) -> tuple[list[tuple[str, ParsedNote, dict | None]], set[str]]:
    changes = []
    seen = set()
    for note in notes:
        page_id = notion_id(note.source_path)
        if not page_id:
            raise ValueError(f"Exported page lacks a Notion ID: {note.source_path}")
        if page_id in seen:
            raise ValueError(f"Duplicate Notion page ID in export: {page_id}")
        seen.add(page_id)
        old = existing.get(page_id)
        if old is None:
            kind = "new"
        elif old["title"] != note.title or old["content"] != note.content:
            kind = "reindex"
        elif old["course"] != note.course or old["source_path"] != note.source_path:
            kind = "metadata"
        else:
            continue
        changes.append((kind, note, old))
    return changes, set(existing) - seen


def save_change(connection, kind: str, note: ParsedNote, old: dict | None) -> None:
    note_id = old["id"] if old else uuid.uuid4()
    needs_embeddings = kind in {"new", "reindex"}
    chunks = chunk_note(note.title, note.content) if needs_embeddings else []
    embeddings = embed_texts([chunk.text for chunk in chunks]) if chunks else []

    with connection:
        with connection.cursor() as cursor:
            if old:
                cursor.execute("""
                    UPDATE notes SET title=%s, course=%s, source_path=%s,
                        raw_content=%s, updated_at=now() WHERE id=%s
                """, (note.title, note.course, note.source_path, note.content, note_id))
                if needs_embeddings:
                    cursor.execute("DELETE FROM chunks WHERE note_id=%s", (note_id,))
            else:
                cursor.execute("""
                    INSERT INTO notes (id, title, course, source_path, raw_content)
                    VALUES (%s, %s, %s, %s, %s)
                """, (note_id, note.title, note.course, note.source_path, note.content))

            if chunks:
                execute_values(cursor, """
                    INSERT INTO chunks (id, note_id, chunk_index, text, heading, token_count, embedding)
                    VALUES %s
                """, [
                    (uuid.uuid4(), note_id, chunk.chunk_index, chunk.text,
                     chunk.heading, chunk.token_count, embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ], template="(%s, %s, %s, %s, %s, %s, %s::vector)")


def run(export: Path, apply: bool) -> None:
    with export_directory(export) as extracted:
        root = find_notes_root(extracted)
        notes = parse_export(str(root), include_ocr=True)
        if len(notes) < 200:
            raise ValueError(f"Export contains only {len(notes)} notes; refusing a likely partial refresh")

        with closing(get_connection()) as connection:
            existing = read_existing(connection)
            changes, missing = changes_for(notes, existing)
            by_kind = {kind: sum(item[0] == kind for item in changes) for kind in ("new", "reindex", "metadata")}
            print(f"Exported notes: {len(notes)}")
            print(f"Changes: {by_kind['new']} new, {by_kind['reindex']} reindexed, {by_kind['metadata']} moved/renamed")
            print(f"Not in current export: {len(missing)} existing pages (retained unchanged)")
            print(f"Referenced images OCR'd: {sum(note.ocr_images for note in notes)}")
            print(f"Images skipped: {sum(note.skipped_images for note in notes)}")
            for kind, note, old in changes:
                visibility = "private" if old is None else ("public" if old["is_public"] else "private")
                print(f"  {kind:8} [{visibility}] {note.source_path}")

            if not apply:
                print("Dry run only. Nothing in the database was changed.")
                return
            if sum(note.skipped_images for note in notes):
                raise ValueError("Some images could not be OCR'd; review before applying")
            for index, (kind, note, old) in enumerate(changes, 1):
                save_change(connection, kind, note, old)
                print(f"Applied {index}/{len(changes)}: {note.title}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Current PeytzNotes Markdown export ZIP or folder")
    parser.add_argument("--apply", action="store_true", help="Apply reviewed changes to the database")
    args = parser.parse_args()
    run(args.export, args.apply)
