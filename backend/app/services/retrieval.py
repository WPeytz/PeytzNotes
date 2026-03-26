"""Vector search and retrieval logic using pgvector."""

import os
from openai import OpenAI

from app.models.database import async_session
from sqlalchemy import text, bindparam
from sqlalchemy.types import UserDefinedType


EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
client = OpenAI()


class VectorType(UserDefinedType):
    """Custom type so SQLAlchemy handles the ::vector cast for asyncpg."""
    cache_ok = True

    def get_col_spec(self):
        return "vector"

    def bind_expression(self, bindvalue):
        return bindvalue.cast(self)

    def bind_processor(self, dialect):
        def process(value):
            return value  # pass the string through as-is
        return process


async def embed_query(query: str) -> list[float]:
    """Embed a single search query."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=query)
    return response.data[0].embedding


async def search_chunks(
    query: str,
    limit: int = 5,
    course: str | None = None,
) -> list[dict]:
    """Find the most relevant chunks for a query using cosine similarity.

    Returns list of dicts with: chunk_id, text, heading, course, note_title, source_path, similarity
    """
    embedding = await embed_query(query)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    # Build query with optional course filter
    where_clause = ""
    params = {"embedding": embedding_str, "limit": limit}

    if course:
        where_clause = "AND n.course = :course"
        params["course"] = course

    sql = text(f"""
        SELECT
            c.id AS chunk_id,
            c.note_id,
            c.text,
            c.heading,
            n.title AS note_title,
            n.course,
            n.source_path,
            1 - (c.embedding <=> :embedding) AS similarity
        FROM chunks c
        JOIN notes n ON c.note_id = n.id
        WHERE 1=1
        {where_clause}
        ORDER BY c.embedding <=> :embedding
        LIMIT :limit
    """).bindparams(bindparam("embedding", type_=VectorType()))

    async with async_session() as session:
        result = await session.execute(sql, params)
        rows = result.mappings().all()

    return [
        {
            "chunk_id": str(row["chunk_id"]),
            "note_id": str(row["note_id"]),
            "text": row["text"],
            "heading": row["heading"],
            "note_title": row["note_title"],
            "course": row["course"],
            "source_path": row["source_path"],
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]
