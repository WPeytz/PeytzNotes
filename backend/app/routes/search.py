"""Search endpoint — vector similarity search over notes."""

from uuid import UUID
from fastapi import APIRouter, Query, Depends
from app.services.retrieval import search_chunks
from app.rate_limit import check_demo_rate_limit
from app.models.database import async_session
from sqlalchemy import text

router = APIRouter()


@router.get("/search", dependencies=[Depends(check_demo_rate_limit)])
async def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    course: str | None = Query(None, description="Filter by course name"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Semantic search across all notes. Returns ranked chunks with similarity scores."""
    results = await search_chunks(q, limit=limit, course=course)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/notes/{note_id}")
async def get_note(note_id: UUID):
    """Get the full content of a note by ID."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, title, course, source_path, raw_content FROM notes WHERE id = :id AND is_public = TRUE"),
            {"id": str(note_id)},
        )
        row = result.mappings().first()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "id": str(row["id"]),
        "title": row["title"],
        "course": row["course"],
        "source_path": row["source_path"],
        "content": row["raw_content"],
    }


@router.get("/notes")
async def list_notes(
    course: str | None = Query(None, description="Filter by course name"),
):
    """List all notes with id, title, course, source_path (no content)."""
    if course:
        sql = text("SELECT id, title, course, source_path FROM notes WHERE is_public = TRUE AND course = :course ORDER BY created_at DESC")
        params = {"course": course}
    else:
        sql = text("SELECT id, title, course, source_path FROM notes WHERE is_public = TRUE ORDER BY source_path")
        params = {}

    async with async_session() as session:
        result = await session.execute(sql, params)
        rows = result.mappings().all()

    return {
        "notes": [
            {
                "id": str(row["id"]),
                "title": row["title"],
                "course": row["course"],
                "source_path": row["source_path"],
            }
            for row in rows
        ]
    }
