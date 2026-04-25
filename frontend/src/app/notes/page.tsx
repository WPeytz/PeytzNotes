"use client";

import { useEffect } from "react";

export default function NotesPage() {
  useEffect(() => {
    window.open(
      "https://trusting-college-827.notion.site/peytznotes",
      "_blank"
    );
  }, []);

  return (
    <div className="text-center text-gray-500 mt-20">
      <p className="text-lg mb-4">Opening Notion...</p>
      <a
        href="https://trusting-college-827.notion.site/peytznotes"
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 hover:text-blue-300 underline"
      >
        Click here if it didn&apos;t open automatically
      </a>
    </div>
  );
}
