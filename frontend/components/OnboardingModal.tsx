"use client";
import { useState } from "react";
import { Github, Loader2, CheckCircle } from "lucide-react";
import { ingestFull } from "@/lib/api";

interface Props {
  onClose: () => void;
  onIndexed: (repo: string) => void;
}

type Step = "idle" | "ingesting" | "embedding" | "done" | "error";

export default function OnboardingModal({ onClose, onIndexed }: Props) {
  const [url,     setUrl]     = useState("https://github.com/tiangolo/fastapi");
  const [step,    setStep]    = useState<Step>("idle");
  const [message, setMessage] = useState("");

  async function handleIndex() {
    if (!url.trim()) return;
    setStep("ingesting");
    setMessage("Clearing old data + cloning repo...");

    try {
      setMessage("Parsing files, building graph, embedding functions...");
      const result = await ingestFull(url);

      setStep("done");
      onIndexed(url);   // ← tell parent which repo was indexed
      setMessage(
        `Done. ${result.total_functions} functions · ${result.total_edges} edges · ${result.vectors_stored} vectors`
      );
    } catch (err) {
      setStep("error");
      setMessage(String(err));
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 w-full max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <Github size={20} className="text-brand-500" />
          <h2 className="text-base font-medium text-[var(--text-primary)]">
            Index a repository
          </h2>
        </div>

        <p className="text-sm text-[var(--text-muted)] mb-4">
          Paste a public GitHub URL. The engine will parse all source files,
          build the call graph, and create semantic embeddings.
        </p>

        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/user/repo"
          disabled={step !== "idle" && step !== "error"}
          className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-brand-500 mb-3 disabled:opacity-50"
        />

        {/* progress */}
        {step !== "idle" && (
          <div className="mb-4 p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
            <div className="flex items-center gap-2">
              {step === "done" ? (
                <CheckCircle size={16} className="text-[var(--green)]" />
              ) : step === "error" ? (
                <span className="text-red-400 text-sm">✗</span>
              ) : (
                <Loader2 size={16} className="text-brand-500 animate-spin" />
              )}
              <p className="text-sm text-[var(--text-primary)]">{message}</p>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {step === "done" ? (
            <button
              onClick={onClose}
              className="flex-1 bg-[var(--green)] hover:opacity-90 text-white rounded-lg px-4 py-2 text-sm font-medium transition-opacity"
            >
              Start exploring
            </button>
          ) : (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleIndex}
                disabled={step !== "idle" && step !== "error"}
                className="flex-1 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {step !== "idle" && step !== "error" && (
                  <Loader2 size={14} className="animate-spin" />
                )}
                {step === "error" ? "Retry" : "Index repository"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}