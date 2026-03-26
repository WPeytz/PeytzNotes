"""Insert parsed notes and chunks into Postgres."""

import os
import uuid
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/peytznotes")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def upload_note_with_chunks(
    title: str,
    course: str | None,
    source_path: str,
    raw_content: str,
    chunks: list[dict],  # each: {text, heading, chunk_index, token_count, embedding}
) -> uuid.UUID:
    """Insert a note and its chunks in a single transaction."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Insert note
            note_id = uuid.uuid4()
            cur.execute(
                """
                INSERT INTO notes (id, title, course, source_path, raw_content)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(note_id), title, course, source_path, raw_content),
            )

            # Batch insert chunks
            if chunks:
                values = [
                    (
                        str(uuid.uuid4()),
                        str(note_id),
                        c["chunk_index"],
                        c["text"],
                        c["heading"],
                        c["token_count"],
                        c["embedding"],  # pgvector accepts Python lists directly
                    )
                    for c in chunks
                ]
                execute_values(
                    cur,
                    """
                    INSERT INTO chunks (id, note_id, chunk_index, text, heading, token_count, embedding)
                    VALUES %s
                    """,
                    values,
                    template="(%s, %s, %s, %s, %s, %s, %s::vector)",
                )

            conn.commit()
            return note_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def note_exists(source_path: str) -> bool:
    """Check if a note with this source path has already been ingested."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM notes WHERE source_path = %s", (source_path,))
            return cur.fetchone() is not None
    finally:
        conn.close()
