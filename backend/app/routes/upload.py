"""File upload endpoint — ingest PDFs and markdown into the RAG pipeline."""

import os
import re
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from openai import OpenAI

from app.models.database import async_session
from sqlalchemy import text, bindparam
from sqlalchemy.types import UserDefinedType

import tiktoken

router = APIRouter()

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
_enc = tiktoken.get_encoding("cl100k_base")
_openai = OpenAI()

TARGET_TOKENS = 500
MAX_TOKENS = 800
OVERLAP_SENTENCES = 2


class VectorType(UserDefinedType):
    cache_ok = True

    def get_col_spec(self):
        return "vector"

    def bind_expression(self, bindvalue):
        return bindvalue.cast(self)

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process


def count_tokens(t: str) -> int:
    return len(_enc.encode(t))


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using pdfplumber."""
    import pdfplumber
    import io

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def split_into_sections(content: str) -> list[tuple[str | None, str]]:
    """Split markdown by headings into (heading, body) pairs."""
    heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
    sections: list[tuple[str | None, str]] = []
    last_end = 0
    current_heading = None

    for match in heading_pattern.finditer(content):
        text_before = content[last_end:match.start()].strip()
        if text_before:
            sections.append((current_heading, text_before))
        current_heading = match.group(2).strip()
        last_end = match.end()

    remaining = content[last_end:].strip()
    if remaining:
        sections.append((current_heading, remaining))

    if not sections and content.strip():
        sections.append((None, content.strip()))

    return sections


def split_text_into_chunks(t: str, heading: str | None, start_index: int) -> list[dict]:
    """Split text into token-limited chunks with sentence overlap."""
    sentences = re.split(r"(?<=[.!?])\s+", t)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens > MAX_TOKENS and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append({
                "text": chunk_text,
                "heading": heading,
                "chunk_index": start_index + len(chunks),
                "token_count": count_tokens(chunk_text),
            })
            current_sentences = current_sentences[-OVERLAP_SENTENCES:]
            current_tokens = count_tokens(" ".join(current_sentences))

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append({
            "text": chunk_text,
            "heading": heading,
            "chunk_index": start_index + len(chunks),
            "token_count": count_tokens(chunk_text),
        })

    return chunks


def chunk_text(title: str, content: str) -> list[dict]:
    """Chunk content into retrieval-ready pieces with heading context."""
    sections = split_into_sections(content)
    all_chunks = []

    for heading, body in sections:
        prefix_parts = [f"Title: {title}"]
        if heading:
            prefix_parts.append(f"Section: {heading}")
        prefix = " | ".join(prefix_parts) + "\n\n"

        raw_chunks = split_text_into_chunks(body, heading, start_index=len(all_chunks))

        for chunk in raw_chunks:
            chunk["text"] = prefix + chunk["text"]
            chunk["token_count"] = count_tokens(chunk["text"])

        all_chunks.extend(raw_chunks)

    return all_chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts in batches."""
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = _openai.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    course: str = Form(...),
):
    """Upload a PDF or markdown file and ingest it into the RAG pipeline."""
    filename = file.filename or "untitled"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("pdf", "md", "txt", "markdown"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Use PDF, markdown, or text files.",
        )

    file_bytes = await file.read()

    # Extract text content
    if ext == "pdf":
        try:
            content = extract_text_from_pdf(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    else:
        content = file_bytes.decode("utf-8", errors="replace")

    if len(content.strip()) < 50:
        raise HTTPException(status_code=400, detail="File has too little text content to process.")

    # Extract title from first heading or filename
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename.rsplit(".", 1)[0]

    source_path = f"uploads/{course}/{filename}"

    # Check for duplicate
    async with async_session() as session:
        result = await session.execute(
            text("SELECT 1 FROM notes WHERE source_path = :sp"),
            {"sp": source_path},
        )
        if result.first():
            raise HTTPException(status_code=409, detail=f"File '{filename}' already uploaded for this course.")

    # Chunk
    chunks = chunk_text(title, content)
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract any chunks from the file.")

    # Embed
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_texts(chunk_texts)

    # Store in DB
    note_id = uuid.uuid4()

    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO notes (id, title, course, source_path, raw_content)
                VALUES (:id, :title, :course, :source_path, :raw_content)
            """),
            {
                "id": str(note_id),
                "title": title,
                "course": course,
                "source_path": source_path,
                "raw_content": content,
            },
        )

        chunk_stmt = text("""
            INSERT INTO chunks (id, note_id, chunk_index, text, heading, token_count, embedding)
            VALUES (:id, :note_id, :chunk_index, :text, :heading, :token_count, :embedding)
        """).bindparams(bindparam("embedding", type_=VectorType()))

        for chunk, embedding in zip(chunks, embeddings):
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await session.execute(
                chunk_stmt,
                {
                    "id": str(uuid.uuid4()),
                    "note_id": str(note_id),
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "heading": chunk["heading"],
                    "token_count": chunk["token_count"],
                    "embedding": embedding_str,
                },
            )

        await session.commit()

    return {
        "note_id": str(note_id),
        "title": title,
        "course": course,
        "chunks": len(chunks),
        "message": f"Successfully ingested '{title}' with {len(chunks)} chunks.",
    }


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a note and its chunks."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT 1 FROM notes WHERE id = :id"),
            {"id": note_id},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail="Note not found")

        # Chunks cascade-delete via FK
        await session.execute(
            text("DELETE FROM notes WHERE id = :id"),
            {"id": note_id},
        )
        await session.commit()

    return {"message": "Note deleted"}
