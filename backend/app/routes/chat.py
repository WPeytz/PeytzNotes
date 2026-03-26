"""Chat endpoints — RAG-powered Q&A over notes."""

from uuid import UUID
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat import create_chat, chat, get_chat_history

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    course: str | None = None


@router.post("/chats")
async def new_chat():
    """Create a new chat session."""
    return await create_chat()


@router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: UUID, body: ChatRequest):
    """Send a message and get an AI response grounded in your notes."""
    result = await chat(str(chat_id), body.message, course=body.course)
    return result


@router.get("/chats/{chat_id}/messages")
async def list_messages(chat_id: UUID):
    """Get full message history for a chat."""
    messages = await get_chat_history(str(chat_id))
    return {"chat_id": str(chat_id), "messages": messages}
