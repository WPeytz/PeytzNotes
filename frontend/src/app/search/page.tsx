"use client";

import { useState } from "react";
import Link from "next/link";
import { search, SearchResult } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await search(query.trim());
      setResults(data.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
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
          <Link
            key={result.chunk_id}
            href={`/notes/${result.note_id}${result.heading ? `?section=${encodeURIComponent(result.heading)}` : ""}`}
            className="block bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-blue-500/50 transition-colors"
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
          </Link>
        ))}
      </div>
    </div>
  );
}
