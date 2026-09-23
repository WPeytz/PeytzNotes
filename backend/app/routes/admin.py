"""Owner-only review and publication of demo notes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import require_admin
from app.models.database import async_session

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


class VisibilityUpdate(BaseModel):
    is_public: bool


@router.get("/notes")
async def list_all_notes():
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT id, title, course, source_path, is_public
            FROM notes ORDER BY course NULLS LAST, title
        """))
        return {"notes": [
            {"id": str(row.id), "title": row.title, "course": row.course,
             "source_path": row.source_path, "is_public": row.is_public}
            for row in result
        ]}


@router.get("/notes/{note_id}")
async def get_any_note(note_id: UUID):
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT id, title, course, source_path, raw_content, is_public
            FROM notes WHERE id = :id
        """), {"id": str(note_id)})
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"id": str(row.id), "title": row.title, "course": row.course,
                "source_path": row.source_path, "content": row.raw_content,
                "is_public": row.is_public}


@router.patch("/notes/{note_id}/visibility")
async def set_note_visibility(note_id: UUID, body: VisibilityUpdate):
    async with async_session() as session:
        result = await session.execute(text("""
            UPDATE notes SET is_public = :is_public, updated_at = now()
            WHERE id = :id RETURNING id, is_public
        """), {"id": str(note_id), "is_public": body.is_public})
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Note not found")
        await session.commit()
    return {"id": str(row.id), "is_public": row.is_public}
