"use client";

import { useState } from "react";
import Markdown from "@/components/Markdown";
import { search, getNote, SearchResult, NoteDetail } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [openNote, setOpenNote] = useState<NoteDetail | null>(null);
  const [noteLoading, setNoteLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setSearched(true);
    setOpenNote(null);
    try {
      const data = await search(query.trim());
      setResults(data.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleOpenNote(noteId: string) {
    setNoteLoading(true);
    try {
      const note = await getNote(noteId);
      setOpenNote(note);
    } catch {
      // ignore
    } finally {
      setNoteLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Search notes</h1>

      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search across all your notes..."
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-3 rounded-lg text-sm font-medium"
        >
          Search
        </button>
      </form>

      {loading && <p className="text-gray-500 animate-pulse">Searching...</p>}

      {!loading && searched && results.length === 0 && (
        <p className="text-gray-500">No results found.</p>
      )}

      <div className="space-y-4">
        {results.map((result) => (
          <div
            key={result.chunk_id}
            onClick={() => handleOpenNote(result.note_id)}
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 cursor-pointer hover:border-blue-500/50 transition-colors"
          >
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-blue-400 font-medium">{result.note_title}</h2>
              {result.course && (
                <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">
                  {result.course}
                </span>
              )}
              <span className="text-xs text-gray-600 ml-auto">
                {(result.similarity * 100).toFixed(0)}% match
              </span>
            </div>

            {result.heading && (
              <p className="text-xs text-gray-500 mb-2">Section: {result.heading}</p>
            )}

            <p className="text-sm text-gray-300 line-clamp-3">{result.text}</p>
          </div>
        ))}
      </div>

      {/* Full note modal */}
      {(openNote || noteLoading) && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center pt-12 px-4"
          onClick={() => setOpenNote(null)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl max-h-[80vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {noteLoading ? (
              <p className="text-gray-500 animate-pulse">Loading note...</p>
            ) : openNote ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-semibold">{openNote.title}</h2>
                    {openNote.course && (
                      <span className="text-xs text-gray-400">{openNote.course}</span>
                    )}
                  </div>
                  <button
                    onClick={() => setOpenNote(null)}
                    className="text-gray-500 hover:text-white text-2xl leading-none px-2"
                  >
                    &times;
                  </button>
                </div>
                <div className="prose prose-invert prose-sm max-w-none">
                  <Markdown>{openNote.content}</Markdown>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
