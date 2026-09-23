"""Chat endpoints — RAG-powered Q&A over notes."""

from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.chat import create_chat, chat, get_chat_history
from app.rate_limit import check_demo_rate_limit
from app.auth import require_admin

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    course: str | None = None


@router.post("/chats", dependencies=[Depends(check_demo_rate_limit)])
async def new_chat():
    """Create a new chat session."""
    return await create_chat()


@router.post("/chats/{chat_id}/messages", dependencies=[Depends(check_demo_rate_limit)])
async def send_message(chat_id: UUID, body: ChatRequest):
    """Send a message and get an AI response grounded in your notes."""
    result = await chat(str(chat_id), body.message, course=body.course)
    return result


@router.get("/chats/{chat_id}/messages", dependencies=[Depends(require_admin)])
async def list_messages(chat_id: UUID):
    """Get full message history for a chat."""
    messages = await get_chat_history(str(chat_id))
    return {"chat_id": str(chat_id), "messages": messages}
