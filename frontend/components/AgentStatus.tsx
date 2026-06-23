"use client";
import { useEffect, useState } from "react";

interface Status {
  neo4j:  boolean;
  qdrant: boolean;
  claude: boolean;
}

export default function AgentStatus({ lastIntent }: { lastIntent: string }) {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    fetch("/http://localhost:8000/")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});
  }, []);

  const stores = [
    { key: "neo4j",  label: "Neo4j graph",     used: ["structural", "historical", "hybrid", "full"] },
    { key: "qdrant", label: "Qdrant vectors",   used: ["semantic",   "hybrid",     "full"] },
    { key: "claude", label: "LLM explainer",    used: ["structural", "semantic",   "historical", "hybrid", "full"] },
  ];

  return (
    <div className="p-4">
      <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">
        Agent status
      </p>
      <div className="space-y-2">
        {stores.map((s) => {
          const connected = status?.[s.key as keyof Status];
          const active    = lastIntent && s.used.includes(lastIntent);
          return (
            <div
              key={s.key}
              className={`flex items-center justify-between p-2 rounded-lg border transition-colors ${
                active
                  ? "border-[var(--green)] bg-green-900/10"
                  : "border-[var(--border)] bg-transparent"
              }`}
            >
              <span className="text-xs text-[var(--text-primary)]">{s.label}</span>
              <span className={`text-xs font-mono ${
                connected === undefined ? "text-[var(--text-muted)]" :
                connected ? "text-[var(--green)]" : "text-red-400"
              }`}>
                {connected === undefined ? "..." : connected ? "✓" : "✗"}
              </span>
            </div>
          );
        })}
      </div>

      {lastIntent && (
        <div className="mt-4 p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
          <p className="text-xs text-[var(--text-muted)] mb-1">Last query routed to</p>
          <p className="text-xs text-[var(--brand-light)] font-medium capitalize">{lastIntent}</p>
        </div>
      )}
    </div>
  );
}