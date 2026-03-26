"""RAG chat service — retrieve context, build prompt, call LLM."""

import json
import os
import uuid
from openai import OpenAI

from app.services.retrieval import search_chunks
from app.models.database import async_session
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB

from app.services.prompts import (
    CHAT_SYSTEM,
    EXAM_SUMMARY_SYSTEM,
    EXAM_SUMMARY_USER,
    FLASHCARD_SYSTEM,
    FLASHCARD_USER,
)

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
client = OpenAI()


def build_context_prompt(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = f"[Source {i}: {chunk['note_title']}"
        if chunk["course"]:
            source += f" — {chunk['course']}"
        source += "]"
        context_parts.append(f"{source}\n{chunk['text']}")

    return "--- NOTES CONTEXT ---\n\n" + "\n\n---\n\n".join(context_parts)


async def create_chat() -> dict:
    """Create a new chat session."""
    chat_id = uuid.uuid4()
    async with async_session() as session:
        await session.execute(
            text("INSERT INTO chats (id) VALUES (:id)"),
            {"id": str(chat_id)},
        )
        await session.commit()
    return {"chat_id": str(chat_id)}


async def get_chat_history(chat_id: str) -> list[dict]:
    """Fetch previous messages in a chat for multi-turn context."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT role, content FROM messages WHERE chat_id = :chat_id ORDER BY created_at"),
            {"chat_id": chat_id},
        )
        return [{"role": row["role"], "content": row["content"]} for row in result.mappings()]


async def save_message(chat_id: str, role: str, content: str, sources: list[dict] | None = None):
    """Persist a message to the database."""
    stmt = text("""
        INSERT INTO messages (id, chat_id, role, content, sources)
        VALUES (:id, :chat_id, :role, :content, :sources)
    """).bindparams(bindparam("sources", type_=JSONB))

    async with async_session() as session:
        await session.execute(
            stmt,
            {
                "id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "role": role,
                "content": content,
                "sources": sources,  # SQLAlchemy handles JSONB serialization
            },
        )
        # Auto-set chat title from first user message
        if role == "user":
            await session.execute(
                text("UPDATE chats SET title = :title WHERE id = :id AND title IS NULL"),
                {"title": content[:100], "id": chat_id},
            )
        await session.commit()


async def chat(chat_id: str, user_message: str, course: str | None = None) -> dict:
    """Full RAG pipeline: retrieve → prompt → LLM → save → respond.

    Returns: {answer, sources}
    """
    # 1. Retrieve relevant chunks
    chunks = await search_chunks(user_message, limit=5, course=course)

    # 2. Build messages array with history + new context
    history = await get_chat_history(chat_id)
    context_prompt = build_context_prompt(chunks)

    messages = [{"role": "system", "content": CHAT_SYSTEM}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"{context_prompt}\n\n--- QUESTION ---\n{user_message}",
    })

    # 3. Call LLM
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.3,  # lower = more factual
        max_tokens=1500,
    )
    answer = response.choices[0].message.content

    # 4. Build source references
    sources = [
        {
            "chunk_id": c["chunk_id"],
            "note_title": c["note_title"],
            "course": c["course"],
            "text_preview": c["text"][:200],
            "similarity": c["similarity"],
        }
        for c in chunks
    ]

    # 5. Save messages to DB
    await save_message(chat_id, "user", user_message)
    await save_message(chat_id, "assistant", answer, sources)

    return {"answer": answer, "sources": sources}


async def generate_exam_summary(course: str) -> dict:
    """Generate an exam-ready summary for a course.

    Retrieves more chunks (15) to get broad coverage of the course material.
    """
    # Use the course name as the search query to get representative content
    chunks = await search_chunks(course, limit=15, course=course)
    context = build_context_prompt(chunks)

    messages = [
        {"role": "system", "content": EXAM_SUMMARY_SYSTEM},
        {"role": "user", "content": EXAM_SUMMARY_USER.format(context=context, course=course)},
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=3000,
    )

    sources = [
        {
            "chunk_id": c["chunk_id"],
            "note_title": c["note_title"],
            "course": c["course"],
            "text_preview": c["text"][:200],
            "similarity": c["similarity"],
        }
        for c in chunks
    ]

    return {"summary": response.choices[0].message.content, "sources": sources}


async def generate_flashcards(course: str) -> dict:
    """Generate flashcards from course notes.

    Retrieves 10 chunks to cover key concepts.
    """
    chunks = await search_chunks(course, limit=10, course=course)
    context = build_context_prompt(chunks)

    messages = [
        {"role": "system", "content": FLASHCARD_SYSTEM},
        {"role": "user", "content": FLASHCARD_USER.format(context=context, course=course)},
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,  # slightly higher for variety
        max_tokens=3000,
    )

    sources = [
        {
            "chunk_id": c["chunk_id"],
            "note_title": c["note_title"],
            "course": c["course"],
            "text_preview": c["text"][:200],
            "similarity": c["similarity"],
        }
        for c in chunks
    ]

    return {"flashcards": response.choices[0].message.content, "sources": sources}
