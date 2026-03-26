"use client";

import { useState, useRef, useEffect } from "react";
import Markdown from "@/components/Markdown";
import { createChat, sendMessage, Source } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export default function ChatPage() {
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      // Create chat session on first message
      let id = chatId;
      if (!id) {
        const chat = await createChat();
        id = chat.chat_id;
        setChatId(id);
      }

      const response = await sendMessage(id, userMessage);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setChatId(null);
    setMessages([]);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Chat with your notes</h1>
        {messages.length > 0 && (
          <button
            onClick={handleNewChat}
            className="text-sm text-gray-400 hover:text-white border border-gray-700 px-3 py-1 rounded"
          >
            New chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-lg">Ask anything about your notes</p>
            <p className="text-sm mt-2">
              Try: &quot;Summarize my economics notes&quot; or &quot;What is the IS-LM model?&quot;
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            <div
              className={`rounded-lg px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 ml-auto max-w-[80%] w-fit"
                  : "bg-gray-800 max-w-[90%]"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <Markdown>{msg.content}</Markdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>

            {/* Sources */}
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-2 space-y-1">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Sources</p>
                {msg.sources.map((src, j) => (
                  <div
                    key={j}
                    className="text-xs bg-gray-900 border border-gray-800 rounded px-3 py-2"
                  >
                    <span className="text-blue-400">{src.note_title}</span>
                    {src.course && (
                      <span className="text-gray-500 ml-2">({src.course})</span>
                    )}
                    <span className="text-gray-600 ml-2">
                      {(src.similarity * 100).toFixed(0)}% match
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="bg-gray-800 rounded-lg px-4 py-3 max-w-[90%] animate-pulse">
            Thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3 pt-4 border-t border-gray-800">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your notes..."
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 px-6 py-3 rounded-lg text-sm font-medium"
        >
          Send
        </button>
      </form>
    </div>
  );
}
