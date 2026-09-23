"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listNotes, NoteSummary } from "@/lib/api";
import { buildNotesTree, filterNotesTree, noteNameSort, NoteFolder } from "./tree";

function NoteLink({ note, overview = false }: { note: NoteSummary; overview?: boolean }) {
  return (
    <li>
      <Link
        className="block rounded-md px-2 py-1.5 text-sm text-blue-400 hover:bg-gray-800 hover:text-blue-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
        href={`/notes/${note.id}`}
        aria-label={overview ? `${note.title} overview` : undefined}
      >
        {overview ? "Overview" : note.title}
      </Link>
    </li>
  );
}

function Folder({ folder, depth, searching }: {
  folder: NoteFolder;
  depth: number;
  searching: boolean;
}) {
  const entries = [
    ...[...folder.folders.values()].map((child) => ({ kind: "folder" as const, name: child.name, child })),
    ...folder.notes.map((note) => ({ kind: "note" as const, name: note.title, note })),
  ].sort((a, b) => noteNameSort.compare(a.name, b.name));

  return (
    <details
      open={searching || depth === 0}
      className={depth === 0
        ? "rounded-xl border border-gray-800 bg-gray-900/60"
        : "rounded-lg border border-gray-800/80 bg-gray-900/40"}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-4 py-3 hover:bg-gray-800/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 [&::-webkit-details-marker]:hidden">
        <span className={depth === 0 ? "font-semibold text-gray-100" : "font-medium text-gray-200"}>
          {folder.name}
        </span>
        <span className="flex shrink-0 items-center gap-3 text-xs text-gray-400">
          {folder.count} {folder.count === 1 ? "page" : "pages"}
          <span aria-hidden="true" className="text-base">⌄</span>
        </span>
      </summary>
      <div className="border-t border-gray-800 px-3 py-3">
        {folder.overview && (
          <ul className="mb-2">
            <NoteLink note={folder.overview} overview />
          </ul>
        )}
        <div className="space-y-2">
          {entries.map((entry) => entry.kind === "folder" ? (
            <Folder
              key={entry.child.path}
              folder={entry.child}
              depth={depth + 1}
              searching={searching}
            />
          ) : (
            <ul key={entry.note.id} className={depth === 0 ? "rounded-lg border border-gray-800/80 bg-gray-900/40 p-2" : ""}>
              <NoteLink note={entry.note} />
            </ul>
          ))}
        </div>
      </div>
    </details>
  );
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

  const tree = useMemo(() => {
    const root = buildNotesTree(notes);
    return filterNotesTree(root, query);
  }, [notes, query]);
  const collections = [...(tree?.folders.values() || [])]
    .sort((a, b) => noteNameSort.compare(a.name, b.name));

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-2 text-2xl font-semibold">Browse notes</h1>
      <p className="mb-6 text-sm text-gray-400">
        Explore {notes.length} published pages by subject, course, and topic.
      </p>
      <label className="mb-6 block">
        <span className="sr-only">Filter notes</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by note, course, or topic..."
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
        />
      </label>
      {loading && <p className="text-gray-400">Loading notes...</p>}
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {!loading && !error && notes.length === 0 && (
        <p className="text-gray-400">No notes have been published for the demo yet.</p>
      )}
      {!loading && !error && notes.length > 0 && collections.length === 0 && (
        <p className="text-gray-400">No notes match that filter.</p>
      )}
      <div className="space-y-4">
        {collections.map((folder) => (
          <Folder key={folder.path} folder={folder} depth={0} searching={Boolean(query.trim())} />
        ))}
        {tree?.notes.map((note) => <ul key={note.id}><NoteLink note={note} /></ul>)}
      </div>
    </div>
  );
}
