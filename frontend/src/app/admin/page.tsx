"use client";

import { useState } from "react";
import Markdown from "@/components/Markdown";
import {
  getManagedNote,
  listManagedNotes,
  ManagedNote,
  NoteDetail,
  setNoteVisibility,
  uploadFile,
  deleteNote,
} from "@/lib/api";

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState("");
  const [notes, setNotes] = useState<ManagedNote[]>([]);
  const [authenticated, setAuthenticated] = useState(false);
  const [selectedNote, setSelectedNote] = useState<NoteDetail | null>(null);
  const [course, setCourse] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setBusy(true);
    setMessage("");
    try {
      setNotes(await listManagedNotes(adminKey));
      setAuthenticated(true);
    } catch (error) {
      setAuthenticated(false);
      setMessage(error instanceof Error ? error.message : "Could not load notes");
    } finally {
      setBusy(false);
    }
  }

  async function preview(noteId: string) {
    setMessage("");
    try {
      setSelectedNote(await getManagedNote(adminKey, noteId));
    } catch {
      setMessage("Could not open note");
    }
  }

  async function toggle(note: ManagedNote) {
    setBusy(true);
    setMessage("");
    try {
      await setNoteVisibility(adminKey, note.id, !note.is_public);
      setNotes((current) => current.map((item) =>
        item.id === note.id ? { ...item, is_public: !item.is_public } : item
      ));
    } catch {
      setMessage("Could not update publication status");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(file: File) {
    if (!course.trim()) {
      setMessage("Enter a course name before uploading.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const result = await uploadFile(file, course.trim(), adminKey);
      setMessage(`${result.title} uploaded privately. Review it before publishing.`);
      setNotes(await listManagedNotes(adminKey));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function remove(note: ManagedNote) {
    if (!window.confirm(`Permanently delete “${note.title}” and its indexed sections?`)) return;
    setBusy(true);
    setMessage("");
    try {
      await deleteNote(note.id, adminKey);
      setNotes((current) => current.filter((item) => item.id !== note.id));
      if (selectedNote?.id === note.id) setSelectedNote(null);
    } catch {
      setMessage("Could not delete note");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Manage demo notes</h1>
      <p className="text-sm text-gray-400 mb-6">New and existing notes are private until you publish them here.</p>
      <form onSubmit={(event) => { event.preventDefault(); load(); }} className="flex flex-wrap gap-3 mb-6">
        <label className="flex-1 min-w-56">
          <span className="sr-only">Owner key</span>
          <input
            type="password"
            autoComplete="off"
            value={adminKey}
            onChange={(event) => {
              setAdminKey(event.target.value);
              setAuthenticated(false);
              setNotes([]);
              setSelectedNote(null);
            }}
            placeholder="Owner key"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5"
          />
        </label>
        <button disabled={!adminKey || busy} className="bg-blue-600 disabled:opacity-50 rounded-lg px-5 py-2.5">
          Load notes
        </button>
      </form>
      {message && <p role="status" className="text-sm text-amber-300 mb-5">{message}</p>}
      {authenticated && (
        <>
          <div className="border border-gray-800 rounded-xl p-4 mb-6 space-y-3">
            <h2 className="font-medium">Upload a note</h2>
            <p className="text-xs text-gray-400">PDF, Markdown, or text. Uploads stay private until reviewed.</p>
            <div className="flex flex-wrap gap-3">
              <input
                value={course}
                onChange={(event) => setCourse(event.target.value)}
                placeholder="Course name"
                className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2"
              />
              <input
                type="file"
                accept=".pdf,.md,.markdown,.txt"
                disabled={busy}
                onChange={(event) => { const file = event.target.files?.[0]; if (file) handleUpload(file); }}
                className="text-sm"
              />
            </div>
          </div>
          <p className="text-sm text-gray-400 mb-3">
            {notes.filter((note) => note.is_public).length} public · {notes.filter((note) => !note.is_public).length} private
          </p>
          <div className="space-y-2">
            {notes.map((note) => (
              <div key={note.id} className="border border-gray-800 rounded-lg px-4 py-3 flex flex-wrap items-center gap-3">
                <div className="flex-1 min-w-52">
                  <p className="font-medium text-sm">{note.title}</p>
                  <p className="text-xs text-gray-500">{note.course || "No course"} · {note.is_public ? "Public" : "Private"}</p>
                </div>
                <button onClick={() => preview(note.id)} className="text-sm text-blue-400 hover:underline">Preview</button>
                <button disabled={busy} onClick={() => toggle(note)} className="text-sm border border-gray-700 px-3 py-1.5 rounded disabled:opacity-50">
                  {note.is_public ? "Unpublish" : "Publish"}
                </button>
                <button disabled={busy} onClick={() => remove(note)} className="text-sm text-red-400 disabled:opacity-50">Delete</button>
              </div>
            ))}
          </div>
        </>
      )}
      {selectedNote && (
        <section className="mt-8 border border-gray-700 rounded-xl p-6 max-h-[70vh] overflow-y-auto">
          <div className="flex justify-between gap-4 mb-4">
            <h2 className="text-lg font-semibold">{selectedNote.title}</h2>
            <button onClick={() => setSelectedNote(null)} aria-label="Close preview" className="text-gray-400">Close</button>
          </div>
          <div className="prose prose-invert max-w-none"><Markdown>{selectedNote.content}</Markdown></div>
        </section>
      )}
    </div>
  );
}
