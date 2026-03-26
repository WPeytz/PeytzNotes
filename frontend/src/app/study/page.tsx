"use client";

import { useState, useEffect } from "react";
import Markdown from "@/components/Markdown";
import { getCourseHierarchy, getExamSummary, getFlashcards, Major, Source } from "@/lib/api";

type Mode = "exam-summary" | "flashcards";

export default function StudyPage() {
  const [hierarchy, setHierarchy] = useState<Major[]>([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [mode, setMode] = useState<Mode>("exam-summary");
  const [content, setContent] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCourseHierarchy().then(setHierarchy).catch(() => {});
  }, []);

  async function handleGenerate() {
    if (!selectedCourse || loading) return;

    setLoading(true);
    setContent("");
    setSources([]);

    try {
      if (mode === "exam-summary") {
        const data = await getExamSummary(selectedCourse);
        setContent(data.summary);
        setSources(data.sources);
      } else {
        const data = await getFlashcards(selectedCourse);
        setContent(data.flashcards);
        setSources(data.sources);
      }
    } catch {
      setContent("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Study tools</h1>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-6">
        {/* Hierarchical course selector */}
        <select
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">Select a course</option>
          {hierarchy.map((major) =>
            major.semesters.map((semester) => (
              <optgroup
                key={`${major.name}-${semester.name}`}
                label={`${major.name} — ${semester.name}`}
              >
                {semester.courses.map((course) => (
                  <option key={course} value={course}>
                    {course}
                  </option>
                ))}
              </optgroup>
            ))
          )}
        </select>

        {/* Mode toggle */}
        <div className="flex rounded-lg border border-gray-700 overflow-hidden">
          <button
            onClick={() => setMode("exam-summary")}
            className={`px-4 py-2.5 text-sm ${
              mode === "exam-summary"
                ? "bg-blue-600 text-white"
                : "bg-gray-900 text-gray-400 hover:text-white"
            }`}
          >
            Exam Summary
          </button>
          <button
            onClick={() => setMode("flashcards")}
            className={`px-4 py-2.5 text-sm ${
              mode === "flashcards"
                ? "bg-blue-600 text-white"
                : "bg-gray-900 text-gray-400 hover:text-white"
            }`}
          >
            Flashcards
          </button>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={!selectedCourse || loading}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-2.5 rounded-lg text-sm font-medium"
        >
          {loading ? "Generating..." : "Generate"}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 animate-pulse">
          <p className="text-gray-500">
            {mode === "exam-summary"
              ? "Creating exam summary... This may take a moment."
              : "Generating flashcards... This may take a moment."}
          </p>
        </div>
      )}

      {/* Output */}
      {content && !loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <div className="prose prose-invert prose-sm max-w-none">
            <Markdown>{content}</Markdown>
          </div>

          {/* Sources */}
          {sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-800">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                Based on {sources.length} note sections
              </p>
              <div className="flex flex-wrap gap-2">
                {sources.map((src, i) => (
                  <span
                    key={i}
                    className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded"
                  >
                    {src.note_title}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
