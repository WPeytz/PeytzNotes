"""Main ingestion script — run this to process a Notion export.

Usage:
    python -m ingestion.run_pipeline /path/to/notion/export
"""

import sys
import os
from dotenv import load_dotenv

# Load .env before importing modules that read env vars
load_dotenv()

from ingestion.notion_parser import parse_export
from ingestion.chunker import chunk_note
from ingestion.embedder import embed_texts
from ingestion.uploader import upload_note_with_chunks, note_exists


def run(export_dir: str):
    # --- Step 1: Parse ---
    print("=" * 60)
    print("STEP 1/4 — Parsing Notion export")
    print("=" * 60)
    notes = parse_export(export_dir)
    if not notes:
        print("No notes found. Check the export path.")
        return

    # --- Step 2: Chunk ---
    print("\n" + "=" * 60)
    print("STEP 2/4 — Chunking notes")
    print("=" * 60)
    all_note_data = []
    total_chunks = 0

    for note in notes:
        # Skip already-ingested notes (idempotent re-runs)
        if note_exists(note.source_path):
            print(f"  Skipping (already ingested): {note.title}")
            continue

        chunks = chunk_note(note.title, note.content)
        total_chunks += len(chunks)
        all_note_data.append((note, chunks))
        print(f"  {note.title}: {len(chunks)} chunks")

    if not all_note_data:
        print("All notes already ingested. Nothing to do.")
        return

    print(f"\nTotal: {len(all_note_data)} notes → {total_chunks} chunks")

    # --- Step 3: Embed ---
    print("\n" + "=" * 60)
    print("STEP 3/4 — Generating embeddings")
    print("=" * 60)
    # Flatten all chunk texts for batch embedding
    all_texts = []
    for _, chunks in all_note_data:
        all_texts.extend([c.text for c in chunks])

    all_embeddings = embed_texts(all_texts)

    # Map embeddings back to their chunks
    embed_idx = 0
    for _, chunks in all_note_data:
        for chunk in chunks:
            chunk.embedding = all_embeddings[embed_idx]
            embed_idx += 1

    # --- Step 4: Upload ---
    print("\n" + "=" * 60)
    print("STEP 4/4 — Uploading to database")
    print("=" * 60)
    for note, chunks in all_note_data:
        chunk_dicts = [
            {
                "text": c.text,
                "heading": c.heading,
                "chunk_index": c.chunk_index,
                "token_count": c.token_count,
                "embedding": c.embedding,
            }
            for c in chunks
        ]
        upload_note_with_chunks(
            title=note.title,
            course=note.course,
            source_path=note.source_path,
            raw_content=note.content,
            chunks=chunk_dicts,
        )
        print(f"  ✓ {note.title} ({len(chunks)} chunks)")

    print(f"\nDone! Ingested {len(all_note_data)} notes with {total_chunks} chunks.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m ingestion.run_pipeline /path/to/notion/export")
        sys.exit(1)
    run(sys.argv[1])
