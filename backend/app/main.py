"""FastAPI application entry point."""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import search, chat, study

app = FastAPI(title="PeytzNotes API", version="0.1.0")

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


@app.get("/health")
async def health():
    return {"status": "ok"}
