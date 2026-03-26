-- PeytzNotes / Recall — Database Schema
-- Requires: PostgreSQL with pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- NOTES — one row per imported Notion page
-- ============================================================
CREATE TABLE notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT NOT NULL,
    course      TEXT,                       -- inferred from folder name
    source_path TEXT NOT NULL,              -- original file path in Notion export
    raw_content TEXT NOT NULL,              -- full markdown content
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_notes_course ON notes (course);

-- ============================================================
-- CHUNKS — embeddings for retrieval
-- ============================================================
CREATE TABLE chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id     UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,           -- ordering within the note
    text        TEXT NOT NULL,
    heading     TEXT,                        -- nearest heading for context
    token_count INTEGER,
    embedding   vector(1536),               -- OpenAI text-embedding-3-small
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- HNSW index for fast approximate nearest-neighbor search
CREATE INDEX idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_chunks_note_id ON chunks (note_id);

-- ============================================================
-- CHATS — conversation sessions
-- ============================================================
CREATE TABLE chats (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT,                       -- auto-generated from first message
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MESSAGES — individual messages within a chat
-- ============================================================
CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id     UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    sources     JSONB,                      -- array of {chunk_id, note_title, text_preview}
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_chat_id ON messages (chat_id);
