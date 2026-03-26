"""Parse Notion markdown export into structured note objects."""

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedNote:
    title: str
    course: str | None
    source_path: str
    content: str


def clean_text(text: str) -> str:
    """Remove Notion export artifacts and normalize whitespace."""
    # Remove Notion ID suffixes from inline references (e.g. "Page Title 32af8b...")
    text = re.sub(r" [a-f0-9]{32}", "", text)
    # Remove image references (we don't embed images)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Remove empty links
    text = re.sub(r"\[]\(.*?\)", "", text)
    # Collapse multiple blank lines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_notion_id(name: str) -> str:
    """Remove trailing Notion hex IDs from folder/file names."""
    return re.sub(r"\s+[a-f0-9]{20,}$", "", name)


def infer_course(file_path: Path, export_root: Path) -> str | None:
    """Infer course name from folder structure.

    Structure: Major/Semester/Course/... → returns "Course"
    Fallback:  Major/Course/...         → returns "Course"
               Course/...               → returns "Course"
    """
    try:
        relative = file_path.relative_to(export_root)
        parts = relative.parts

        # Major/Semester/Course/note.md → course is parts[2]
        if len(parts) > 3:
            return strip_notion_id(parts[2])
        # Major/Course/note.md → course is parts[1]
        if len(parts) > 2:
            return strip_notion_id(parts[1])
        # Course/note.md → course is parts[0]
        if len(parts) > 1:
            return strip_notion_id(parts[0])
    except ValueError:
        pass
    return None


def extract_title(content: str, file_path: Path) -> str:
    """Extract title from first H1 heading, or fall back to filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Use filename without extension and Notion ID suffix
    name = file_path.stem
    # Strip trailing Notion hex IDs (e.g. "My Page 8a3b2c1d...")
    name = re.sub(r"\s+[a-f0-9]{20,}$", "", name)
    return name


def parse_export(export_dir: str) -> list[ParsedNote]:
    """Walk a Notion export directory and return parsed notes.

    Args:
        export_dir: Path to the root of the Notion markdown export.

    Returns:
        List of ParsedNote objects ready for chunking.
    """
    export_root = Path(export_dir)
    if not export_root.is_dir():
        raise FileNotFoundError(f"Export directory not found: {export_dir}")

    notes: list[ParsedNote] = []

    for md_file in sorted(export_root.rglob("*.md")):
        raw = md_file.read_text(encoding="utf-8", errors="replace")
        content = clean_text(raw)

        # Skip near-empty files
        if len(content) < 50:
            continue

        title = extract_title(raw, md_file)
        course = infer_course(md_file, export_root)
        source_path = str(md_file.relative_to(export_root))

        notes.append(ParsedNote(
            title=title,
            course=course,
            source_path=source_path,
            content=content,
        ))

    print(f"Parsed {len(notes)} notes from {export_dir}")
    return notes
