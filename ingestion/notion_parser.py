"""Parse Notion markdown export into structured note objects."""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\((?:<([^>]+)>|([^)]*))\)")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


@dataclass
class ParsedNote:
    title: str
    course: str | None
    source_path: str
    content: str
    ocr_images: int = 0
    skipped_images: int = 0


def image_text(
    raw: str, md_file: Path, export_root: Path, cache: dict[Path, str]
) -> tuple[str, int, int]:
    """OCR local images referenced by a Notion Markdown page."""
    sections: list[str] = []
    recognized = 0
    skipped = 0
    root = export_root.resolve()

    for match in IMAGE_PATTERN.finditer(raw):
        target = (match.group(2) or match.group(3) or "").strip()
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            skipped += 1
            continue
        image_path = (md_file.parent / unquote(parsed.path)).resolve()
        if not image_path.is_relative_to(root) or not image_path.is_file():
            skipped += 1
            continue
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS or image_path.stat().st_size > 25 * 1024 * 1024:
            skipped += 1
            continue

        if image_path not in cache:
            result = subprocess.run(
                ["tesseract", str(image_path), "stdout", "-l",
                 os.getenv("PEYTZNOTES_OCR_LANG", "eng+dan")],
                capture_output=True, text=True, timeout=90, check=False,
            )
            if result.returncode:
                skipped += 1
                continue
            cache[image_path] = result.stdout.strip()

        recognized += 1
        if cache[image_path]:
            label = (match.group(1).strip() or image_path.stem).replace("\n", " ")
            sections.append(f"### {label}\n\n{cache[image_path]}")

    if not sections:
        return "", recognized, skipped
    return "## Text found in images\n\n" + "\n\n".join(sections), recognized, skipped


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


def parse_export(export_dir: str, include_ocr: bool = False) -> list[ParsedNote]:
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
    ocr_cache: dict[Path, str] = {}

    for md_file in sorted(export_root.rglob("*.md")):
        raw = md_file.read_text(encoding="utf-8", errors="replace")
        content = clean_text(raw)
        ocr_content, ocr_images, skipped_images = (
            image_text(raw, md_file, export_root, ocr_cache)
            if include_ocr else ("", 0, 0)
        )
        if ocr_content:
            content = f"{content}\n\n{ocr_content}"

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
            ocr_images=ocr_images,
            skipped_images=skipped_images,
        ))

    print(f"Parsed {len(notes)} notes from {export_dir}")
    return notes
