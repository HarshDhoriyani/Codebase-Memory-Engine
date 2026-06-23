"use client";
import { Message } from "@/hooks/useChat";

const INTENT_COLORS: Record<string, string> = {
  structural: "bg-purple-900/40 text-purple-300 border-purple-700",
  semantic:   "bg-teal-900/40 text-teal-300 border-teal-700",
  historical: "bg-amber-900/40 text-amber-300 border-amber-700",
  hybrid:     "bg-blue-900/40 text-blue-300 border-blue-700",
  full:       "bg-pink-900/40 text-pink-300 border-pink-700",
};

export default function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%]">
        {/* intent badge */}
        {message.intent && (
          <div className="flex gap-2 mb-2 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${INTENT_COLORS[message.intent] || ""}`}>
              {message.intent}
            </span>
            {message.function && (
              <span className="text-xs px-2 py-0.5 rounded-full border border-gray-700 text-gray-400 font-mono">
                {message.function}()
              </span>
            )}
          </div>
        )}

        {/* message body */}
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
          {message.content}
          {message.loading && <span className="cursor" />}
          {!message.content && message.loading && (
            <span className="text-[var(--text-muted)]">Thinking...</span>
          )}
        </div>
      </div>
    </div>
  );
}