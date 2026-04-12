const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Types ---

export interface Source {
  chunk_id: string;
  note_title: string;
  course: string | null;
  text_preview: string;
  similarity: number;
}

export interface SearchResult {
  chunk_id: string;
  note_id: string;
  text: string;
  heading: string | null;
  note_title: string;
  course: string | null;
  source_path: string;
  similarity: number;
}

export interface NoteDetail {
  id: string;
  title: string;
  course: string | null;
  source_path: string;
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

// --- API calls ---

export async function search(
  query: string,
  course?: string,
  limit: number = 5
): Promise<{ query: string; results: SearchResult[]; count: number }> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (course) params.set("course", course);

  const res = await fetch(`${API_BASE}/search?${params}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function createChat(): Promise<{ chat_id: string }> {
  const res = await fetch(`${API_BASE}/chats`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create chat");
  return res.json();
}

export async function sendMessage(
  chatId: string,
  message: string,
  course?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, course: course || null }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export interface Semester {
  name: string;
  courses: string[];
}

export interface Major {
  name: string;
  semesters: Semester[];
}

export async function getCourseHierarchy(): Promise<Major[]> {
  const res = await fetch(`${API_BASE}/courses`);
  if (!res.ok) throw new Error("Failed to fetch courses");
  const data = await res.json();
  return data.hierarchy;
}

export interface NoteSummary {
  id: string;
  title: string;
  course: string | null;
  source_path: string;
}

export async function listNotes(): Promise<NoteSummary[]> {
  const res = await fetch(`${API_BASE}/notes`);
  if (!res.ok) throw new Error("Failed to fetch notes");
  const data = await res.json();
  return data.notes;
}

export async function getNote(noteId: string): Promise<NoteDetail> {
  const res = await fetch(`${API_BASE}/notes/${noteId}`);
  if (!res.ok) throw new Error("Failed to fetch note");
  return res.json();
}

export async function getExamSummary(
  course: string
): Promise<{ summary: string; sources: Source[] }> {
  const res = await fetch(
    `${API_BASE}/study/exam-summary?course=${encodeURIComponent(course)}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to generate summary");
  return res.json();
}

export async function getFlashcards(
  course: string
): Promise<{ flashcards: string; sources: Source[] }> {
  const res = await fetch(
    `${API_BASE}/study/flashcards?course=${encodeURIComponent(course)}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to generate flashcards");
  return res.json();
}

// --- Upload ---

export interface UploadResult {
  note_id: string;
  title: string;
  course: string;
  chunks: number;
  message: string;
}

export async function uploadFile(
  file: File,
  course: string
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("course", course);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function deleteNote(noteId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/notes/${noteId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete note");
}

export async function listCourseNotes(
  course: string
): Promise<NoteSummary[]> {
  const res = await fetch(
    `${API_BASE}/notes?course=${encodeURIComponent(course)}`
  );
  if (!res.ok) throw new Error("Failed to fetch notes");
  const data = await res.json();
  return data.notes;
}
