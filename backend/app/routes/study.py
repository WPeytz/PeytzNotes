"""Study feature endpoints — exam summaries and flashcards."""

import re
from collections import defaultdict
from fastapi import APIRouter, Query
from app.services.chat import generate_exam_summary, generate_flashcards
from app.models.database import async_session
from sqlalchemy import text

router = APIRouter()


def strip_notion_id(name: str) -> str:
    """Remove trailing Notion hex IDs from folder/file names."""
    return re.sub(r"\s+[a-f0-9]{20,}$", "", name)


def is_semester_folder(name: str) -> bool:
    """Check if a folder name looks like a semester (e.g. '1 Semester', '3 Semester')."""
    clean = strip_notion_id(name)
    return bool(re.match(r"^\d+\s+Semester$", clean, re.IGNORECASE))


@router.get("/courses")
async def list_courses():
    """Return course hierarchy: major → semester → courses.

    Handles two structures:
      - Major/Semester/Course/note.md  (Economics)
      - Major/Course/note.md           (Human-Centered AI, no semester layer)
    """
    async with async_session() as session:
        result = await session.execute(
            text("SELECT DISTINCT source_path FROM notes")
        )
        paths = [row[0] for row in result]

    # tree: major → semester → set of courses
    tree: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for path in paths:
        parts = path.split("/")
        if len(parts) < 3:
            continue

        major = strip_notion_id(parts[0])

        if is_semester_folder(parts[1]):
            # Structure: Major/Semester/Course/...
            if len(parts) >= 4:
                semester = strip_notion_id(parts[1])
                course = strip_notion_id(parts[2])
                if not course.endswith(".md"):
                    tree[major][semester].add(course)
        else:
            # Structure: Major/Course/... (no semester layer)
            course = strip_notion_id(parts[1])
            if not course.endswith(".md"):
                tree[major]["Courses"].add(course)

    # Convert to a sorted serializable structure
    hierarchy = []
    for major in sorted(tree):
        semesters = []
        for semester in sorted(tree[major]):
            courses = sorted(tree[major][semester])
            semesters.append({"name": semester, "courses": courses})
        hierarchy.append({"name": major, "semesters": semesters})

    return {"hierarchy": hierarchy}


@router.post("/study/exam-summary")
async def exam_summary(course: str = Query(..., description="Course name")):
    """Generate an exam-ready summary for a specific course."""
    return await generate_exam_summary(course)


@router.post("/study/flashcards")
async def flashcards(course: str = Query(..., description="Course name")):
    """Generate flashcards from a specific course's notes."""
    return await generate_flashcards(course)
