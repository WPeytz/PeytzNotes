"""Tests for safe one-time Notion refresh preparation."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ingestion.notion_parser import parse_export
from ingestion.refresh_pipeline import changes_for, notion_id


class RefreshTests(unittest.TestCase):
    def test_ocr_text_is_attached_to_its_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "AI & Data" / "Deep Learning"
            folder.mkdir(parents=True)
            (folder / "slide.png").write_bytes(b"image")
            page = folder / ("Lecture " + "a" * 32 + ".md")
            page.write_text(
                "# Lecture\n\nA long enough introduction to make this note eligible.\n\n"
                "![Training diagram](slide.png)\n", encoding="utf-8"
            )
            result = subprocess.CompletedProcess([], 0, "Input layer Output layer\n", "")
            with patch("ingestion.notion_parser.subprocess.run", return_value=result):
                notes = parse_export(str(root), include_ocr=True)
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0].ocr_images, 1)
            self.assertIn("Input layer Output layer", notes[0].content)
            self.assertNotIn("![Training diagram]", notes[0].content)

    def test_existing_id_preserves_row_and_recognizes_move(self):
        page_id = "a" * 32
        self.assertEqual(notion_id(f"Course/Page {page_id}.md"), page_id)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            moved = root / "Human-Centered AI" / "Course"
            moved.mkdir(parents=True)
            (moved / f"Page {page_id}.md").write_text(
                "# Page\n\nThis content is long enough to be imported without being skipped.",
                encoding="utf-8",
            )
            note = parse_export(str(root))[0]
            existing = {page_id: {
                "id": "database-id", "title": note.title, "course": note.course,
                "source_path": f"AI & Data/Old Course/Page {page_id}.md",
                "content": note.content, "is_public": True,
            }}
            changes, missing = changes_for([note], existing)
            self.assertEqual(changes[0][0], "metadata")
            self.assertEqual(changes[0][2]["id"], "database-id")
            self.assertFalse(missing)


if __name__ == "__main__":
    unittest.main()
