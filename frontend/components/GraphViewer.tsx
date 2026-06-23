"use client";
import { useRef, useEffect, useState } from "react";
import { Send } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import MessageBubble from "./MessageBubble";

const SUGGESTIONS = [
  "What does the add_api_route function call?",
  "Find functions that handle request validation",
  "Why has the __init__ function changed so many times?",
  "Which functions are most complex in the codebase?",
];

export default function GraphViewer({
  onNodeClick,
}: {
  onNodeClick: (name: string) => void;
}) {
  const { messages, isLoading, lastIntent, sendMessage } = useChat();
  const [input,    setInput]    = useState("");
  const bottomRef               = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (lastIntent) onNodeClick(lastIntent);
  }, [lastIntent, onNodeClick]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput("");
  }

  return (
    <div className="flex flex-col h-full">
      {/* header */}
      <div className="px-4 py-3 border-b border-[var(--border)]">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Chat</h2>
        <p className="text-xs text-[var(--text-muted)]">Ask anything about the codebase</p>
      </div>

      {/* messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-4">
            <p className="text-sm text-[var(--text-muted)] text-center">
              Ask a question about the indexed codebase
            </p>
            <div className="flex flex-col gap-2 w-full max-w-sm">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { sendMessage(s); }}
                  className="text-left text-xs px-3 py-2 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:border-brand-500 hover:text-[var(--text-primary)] transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((m) => <MessageBubble key={m.id} message={m} />)}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* input */}
      <form
        onSubmit={handleSubmit}
        className="p-3 border-t border-[var(--border)] flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the codebase..."
          disabled={isLoading}
          className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-brand-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="p-2 bg-brand-600 rounded-lg hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={16} className="text-white" />
        </button>
      </form>
    </div>
  );
}