"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listNotes, NoteSummary } from "@/lib/api";

function cleanName(name: string): string {
  return name.replace(/\s+[a-f0-9]{20,}$/i, "");
}

function groupLabel(note: NoteSummary): string {
  const parts = note.source_path.split("/");
  if (parts[0] === "uploads") return note.course || "Uploaded notes";
  const major = cleanName(parts[0] || "Other");
  const semester = parts.length >= 4 && /^\d+\s+Semester$/i.test(cleanName(parts[1]))
    ? ` — ${cleanName(parts[1])}`
    : "";
  return `${major}${semester}`;
}

export default function NotesPage() {
  const [notes, setNotes] = useState<NoteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    listNotes().then(setNotes).catch(() => setError("Could not load notes. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  const groups = useMemo(() => {
    const matches = notes.filter((note) =>
      `${note.title} ${note.course || ""}`.toLowerCase().includes(query.toLowerCase())
    );
    const grouped = new Map<string, Map<string, NoteSummary[]>>();
    for (const note of matches) {
      const label = groupLabel(note);
      if (!grouped.has(label)) grouped.set(label, new Map());
      const courses = grouped.get(label)!;
      const course = note.course || "Other notes";
      if (!courses.has(course)) courses.set(course, []);
      courses.get(course)!.push(note);
    }
    return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [notes, query]);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Browse notes</h1>
      <p className="text-sm text-gray-400 mb-6">Explore the notes available in this demo by course.</p>
      <label className="block mb-6">
        <span className="sr-only">Filter notes</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by note or course..."
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
        />
      </label>
      {loading && <p className="text-gray-400">Loading notes...</p>}
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {!loading && !error && notes.length === 0 && (
        <p className="text-gray-400">No notes have been published for the demo yet.</p>
      )}
      {!loading && !error && notes.length > 0 && groups.length === 0 && (
        <p className="text-gray-400">No notes match that filter.</p>
      )}
      <div className="space-y-8">
        {groups.map(([group, courses]) => (
          <section key={group}>
            <h2 className="text-lg font-semibold text-gray-200 mb-4">{group}</h2>
            <div className="space-y-5">
              {[...courses.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([course, items]) => (
                <div key={course} className="border border-gray-800 rounded-xl p-4 bg-gray-900/60">
                  <h3 className="font-medium mb-3">{course}</h3>
                  <ul className="space-y-2">
                    {items.sort((a, b) => a.title.localeCompare(b.title)).map((note) => (
                      <li key={note.id}>
                        <Link className="text-sm text-blue-400 hover:text-blue-300 hover:underline" href={`/notes/${note.id}`}>
                          {note.title}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
