"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Markdown from "@/components/Markdown";
import { getNote, NoteDetail } from "@/lib/api";

export default function NotePage() {
  const { id } = useParams<{ id: string }>();
  const [note, setNote] = useState<NoteDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getNote(id).then(setNote).catch(() => setError("This note is unavailable."));
  }, [id]);

  useEffect(() => {
    if (!note) return;
    const section = new URLSearchParams(window.location.search).get("section");
    if (!section) return;
    const frame = requestAnimationFrame(() => {
      const headings = document.querySelectorAll("article h1, article h2, article h3, article h4");
      const target = [...headings].find((heading) => heading.textContent?.trim() === section);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => cancelAnimationFrame(frame);
  }, [note]);

  return (
    <div className="max-w-4xl mx-auto">
      <Link href="/notes" className="text-sm text-blue-400 hover:underline">← All notes</Link>
      {error && <p role="alert" className="mt-6 text-red-400">{error}</p>}
      {!note && !error && <p className="mt-6 text-gray-400">Loading note...</p>}
      {note && (
        <>
          <h1 className="text-2xl font-semibold mt-6 mb-1">{note.title}</h1>
          {note.course && <p className="text-sm text-gray-400 mb-6">{note.course}</p>}
          <article className="prose prose-invert max-w-none border-t border-gray-800 pt-6">
            <Markdown>{note.content}</Markdown>
          </article>
        </>
      )}
    </div>
  );
}
