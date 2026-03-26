4. Step-by-step build plan

Phase 1 — Data pipeline (MOST IMPORTANT)

Step 1: Export Notion
	•	Export as Markdown + CSV
	•	Keep folder structure

Step 2: Parse notes

Write a parser that:
	•	reads markdown files
	•	extracts:
	•	title
	•	content
	•	file path
	•	optionally infer course from folder name

⸻

Step 3: Chunking

Split notes into chunks:
	•	300–800 tokens
	•	include heading context

Each chunk:

{
  text: "...",
  title: "...",
  course: "...",
  source: "..."
}

Step 4: Embeddings
	•	call embedding API
	•	attach embedding vector

⸻

Step 5: Store in DB

Table: chunks

Columns:
	•	id
	•	text
	•	embedding (vector)
	•	course
	•	title
	•	source

⸻

Phase 2 — Retrieval + API

Endpoint: /search
	•	input: query + optional course
	•	output: top chunks

Endpoint: /chat
	•	retrieve relevant chunks
	•	send to LLM with prompt:
	•	“answer ONLY using these notes”
	•	return answer + sources

⸻

Phase 3 — Frontend

Page 1: Chat
	•	input box
	•	response
	•	sources shown below

Page 2: Search
	•	search bar
	•	filters (course)
	•	result list

⸻

Phase 4 — Study features

Exam summary

Prompt:

“Summarize these notes into an exam-ready guide”

Flashcards

Prompt:

“Generate flashcards (Q/A) from these notes”