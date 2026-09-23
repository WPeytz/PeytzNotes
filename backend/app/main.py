"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.models.database import engine
from app.routes import search, chat, study, upload, admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Existing notes start private until the owner explicitly publishes them.
    async with engine.begin() as connection:
        await connection.execute(text(
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await connection.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_notes_public_course ON notes (is_public, course)"
        ))
        await connection.execute(text(
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS public_demo BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await connection.execute(text("""
            CREATE TABLE IF NOT EXISTS demo_rate_limits (
                client_key TEXT PRIMARY KEY,
                hour_bucket BIGINT NOT NULL,
                request_count INTEGER NOT NULL
            )
        """))
    yield


app = FastAPI(title="PeytzNotes API", version="0.1.0", lifespan=lifespan)

# Allow Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://peytznotes.dk",
        "https://www.peytznotes.dk",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, tags=["search"])
app.include_router(chat.router, tags=["chat"])
app.include_router(study.router, tags=["study"])
app.include_router(upload.router, tags=["upload"])
app.include_router(admin.router, tags=["admin"])


@app.middleware("http")
async def prevent_api_caching(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}
