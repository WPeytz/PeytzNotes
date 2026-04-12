"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Markdown from "@/components/Markdown";
import {
  uploadFile,
  deleteNote,
  listCourseNotes,
  getExamSummary,
  getFlashcards,
  createChat,
  sendMessage,
  NoteSummary,
  Source,
  UploadResult,
} from "@/lib/api";

const COURSE_NAME = "Introduction to Deep Learning in Computer Vision";

type Tab = "materials" | "summary" | "flashcards" | "chat";

export default function DeepLearningCVPage() {
  // --- Tab state ---
  const [activeTab, setActiveTab] = useState<Tab>("materials");

  // --- Materials state ---
  const [notes, setNotes] = useState<NoteSummary[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Study state ---
  const [studyContent, setStudyContent] = useState("");
  const [studySources, setStudySources] = useState<Source[]>([]);
  const [studyLoading, setStudyLoading] = useState(false);

  // --- Chat state ---
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string; sources?: Source[] }[]
  >([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const loadNotes = useCallback(async () => {
    try {
      const data = await listCourseNotes(COURSE_NAME);
      setNotes(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- Upload handlers ---
  async function handleFiles(files: FileList | File[]) {
    setUploading(true);
    setUploadMessage("");

    const results: string[] = [];
    for (const file of Array.from(files)) {
      try {
        const res = await uploadFile(file, COURSE_NAME);
        results.push(`${res.title}: ${res.chunks} chunks`);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Upload failed";
        results.push(`${file.name}: ${msg}`);
      }
    }

    setUploadMessage(results.join("\n"));
    setUploading(false);
    loadNotes();
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) {
      handleFiles(e.dataTransfer.files);
    }
  }

  async function handleDelete(noteId: string) {
    try {
      await deleteNote(noteId);
      loadNotes();
    } catch {
      // ignore
    }
  }

  // --- Study handlers ---
  async function handleGenerateSummary() {
    setStudyLoading(true);
    setStudyContent("");
    setStudySources([]);
    try {
      const data = await getExamSummary(COURSE_NAME);
      setStudyContent(data.summary);
      setStudySources(data.sources);
    } catch {
      setStudyContent("Failed to generate summary. Make sure you have uploaded course materials.");
    } finally {
      setStudyLoading(false);
    }
  }

  async function handleGenerateFlashcards() {
    setStudyLoading(true);
    setStudyContent("");
    setStudySources([]);
    try {
      const data = await getFlashcards(COURSE_NAME);
      setStudyContent(data.flashcards);
      setStudySources(data.sources);
    } catch {
      setStudyContent(
        "Failed to generate flashcards. Make sure you have uploaded course materials."
      );
    } finally {
      setStudyLoading(false);
    }
  }

  // --- Chat handlers ---
  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatLoading(true);

    try {
      let currentChatId = chatId;
      if (!currentChatId) {
        const chat = await createChat();
        currentChatId = chat.chat_id;
        setChatId(currentChatId);
      }

      const res = await sendMessage(currentChatId, userMsg, COURSE_NAME);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "materials", label: "Materials" },
    { key: "summary", label: "Exam Summary" },
    { key: "flashcards", label: "Flashcards" },
    { key: "chat", label: "Q&A Chat" },
  ];

  return (
    <div>
      <h1 className="text-xl font-semibold mb-1">
        Introduction to Deep Learning in Computer Vision
      </h1>
      <p className="text-sm text-gray-400 mb-6">Reexam preparation</p>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? "border-blue-500 text-white"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── Materials Tab ─── */}
      {activeTab === "materials" && (
        <div>
          {/* Upload area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragOver
                ? "border-blue-500 bg-blue-500/10"
                : "border-gray-700 hover:border-gray-500"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.md,.txt,.markdown"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.length) handleFiles(e.target.files);
              }}
            />
            <p className="text-gray-400 text-sm">
              {uploading
                ? "Uploading and processing..."
                : "Drop PDF or markdown files here, or click to browse"}
            </p>
            <p className="text-gray-600 text-xs mt-1">
              Supports .pdf, .md, .txt
            </p>
          </div>

          {/* Upload feedback */}
          {uploadMessage && (
            <pre className="mt-3 text-xs text-gray-400 bg-gray-900 border border-gray-800 rounded-lg p-3 whitespace-pre-wrap">
              {uploadMessage}
            </pre>
          )}

          {/* Materials list */}
          <div className="mt-6">
            <h2 className="text-sm font-medium text-gray-300 mb-3">
              Uploaded materials ({notes.length})
            </h2>
            {notes.length === 0 ? (
              <p className="text-sm text-gray-500">
                No materials uploaded yet. Upload lecture slides, notes, or
                readings to get started.
              </p>
            ) : (
              <div className="space-y-2">
                {notes.map((note) => (
                  <div
                    key={note.id}
                    className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3"
                  >
                    <div>
                      <p className="text-sm text-gray-200">{note.title}</p>
                      <p className="text-xs text-gray-500">
                        {note.source_path}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(note.id)}
                      className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Exam Summary Tab ─── */}
      {activeTab === "summary" && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <button
              onClick={handleGenerateSummary}
              disabled={studyLoading}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-2.5 rounded-lg text-sm font-medium"
            >
              {studyLoading ? "Generating..." : "Generate Exam Summary"}
            </button>
            {notes.length === 0 && (
              <span className="text-xs text-gray-500">
                Upload materials first in the Materials tab
              </span>
            )}
          </div>

          {studyLoading && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 animate-pulse">
              <p className="text-gray-500">
                Creating exam summary from your materials...
              </p>
            </div>
          )}

          {studyContent && !studyLoading && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="prose prose-invert prose-sm max-w-none">
                <Markdown>{studyContent}</Markdown>
              </div>
              {studySources.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                    Based on {studySources.length} note sections
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {studySources.map((src, i) => (
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
      )}

      {/* ─── Flashcards Tab ─── */}
      {activeTab === "flashcards" && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <button
              onClick={handleGenerateFlashcards}
              disabled={studyLoading}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-2.5 rounded-lg text-sm font-medium"
            >
              {studyLoading ? "Generating..." : "Generate Flashcards"}
            </button>
            {notes.length === 0 && (
              <span className="text-xs text-gray-500">
                Upload materials first in the Materials tab
              </span>
            )}
          </div>

          {studyLoading && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 animate-pulse">
              <p className="text-gray-500">
                Generating flashcards from your materials...
              </p>
            </div>
          )}

          {studyContent && !studyLoading && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="prose prose-invert prose-sm max-w-none">
                <Markdown>{studyContent}</Markdown>
              </div>
              {studySources.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                    Based on {studySources.length} note sections
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {studySources.map((src, i) => (
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
      )}

      {/* ─── Chat Tab ─── */}
      {activeTab === "chat" && (
        <div className="flex flex-col" style={{ height: "calc(100vh - 280px)" }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 text-sm">
                  Ask questions about your course materials.
                </p>
                <p className="text-gray-600 text-xs mt-1">
                  e.g. &quot;Explain convolutional neural networks&quot; or
                  &quot;What are the key differences between ResNet and VGG?&quot;
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`${
                  msg.role === "user" ? "flex justify-end" : ""
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-900 border border-gray-800"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                  ) : (
                    <p className="text-sm">{msg.content}</p>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-800">
                      <div className="flex flex-wrap gap-1">
                        {msg.sources.map((src, j) => (
                          <span
                            key={j}
                            className="text-xs bg-gray-800 text-gray-500 px-1.5 py-0.5 rounded"
                          >
                            {src.note_title}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 max-w-[85%] animate-pulse">
                <p className="text-gray-500 text-sm">Thinking...</p>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about your course materials..."
              className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || chatLoading}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-2.5 rounded-lg text-sm font-medium"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
