2. System Architecture

High-level flow
Notion Export → Parser → Chunking → Embeddings → DB (pgvector)
                                              ↓
User Query → Retrieval → LLM → Response + Sources

Components

Ingestion pipeline (Python)
	•	parse Notion export
	•	clean text
	•	chunk notes
	•	generate embeddings
	•	store in DB

Backend (FastAPI)
	•	search endpoint
	•	chat endpoint
	•	summary endpoint
	•	flashcard endpoint

Frontend (Next.js)
	•	chat UI
	•	search UI
	•	filters
	•	result display with sources

Database (Supabase Postgres)
	•	notes
	•	chunks (with embeddings)
	•	chats