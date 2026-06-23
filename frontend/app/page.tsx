"use client";
import { useState } from "react";
import { Github, BarChart2, MessageSquare } from "lucide-react";
import ChatPanel       from "@/components/ChatPanel";
import GraphViewer     from "@/components/GraphViewer";
import AgentStatus     from "@/components/AgentStatus";
import OnboardingModal from "@/components/OnboardingModal";

export default function Home() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [lastIntent,     setLastIntent]     = useState("");
  const [activeTab,      setActiveTab]      = useState<"graph" | "stats">("graph");
  const [clickedNode,    setClickedNode]    = useState<string | null>(null);
  const [currentRepo, setCurrentRepo]       = useState<string>("");

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-primary)]">

      {/* top bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">CM</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-[var(--text-primary)]">
              Codebase Memory Engine
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              Ask questions about any codebase
            </p>
          </div>
        </div>

        {currentRepo && (
          <span className="text-xs text-[var(--text-muted)] font-mono truncate max-w-[200px] hidden sm:block">
            📦 {currentRepo.replace("https://github.com/", "")}
          </span>
        )}
        
        <button
          onClick={() => setShowOnboarding(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 rounded-lg text-xs text-white font-medium transition-colors"
        >
          <Github size={14} />
          Index repo
        </button>
      </header>

      {/* main layout */}
      <div className="flex flex-1 overflow-hidden">

        {/* left — chat */}
        <div className="w-[380px] shrink-0 border-r border-[var(--border)] flex flex-col bg-[var(--bg-secondary)] overflow-hidden">
          <ChatPanel onIntentChange={(intent) => setLastIntent(intent)} />
        </div>

        {/* center — graph */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* tab bar */}
          <div className="flex border-b border-[var(--border)] px-2 pt-2 bg-[var(--bg-secondary)] shrink-0">
            {[
              { key: "graph", label: "Call graph",  icon: BarChart2 },
              { key: "stats", label: "Chat context", icon: MessageSquare },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as "graph" | "stats")}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-lg transition-colors ${
                  activeTab === key
                    ? "text-[var(--text-primary)] bg-[var(--bg-primary)] border border-b-0 border-[var(--border)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                <Icon size={13} />
                {label}
              </button>
            ))}
          </div>

          <div className="flex-1 bg-[var(--bg-primary)] overflow-hidden">
            {activeTab === "graph" && (
              <GraphViewer
                onNodeClick={(name) => {
                  setClickedNode(name);
                }}
              />
            )}
            {activeTab === "stats" && (
              <div className="p-4 h-full overflow-y-auto">
                <p className="text-xs text-[var(--text-muted)] mb-2">Last clicked node</p>
                {clickedNode ? (
                  <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-3">
                    <p className="text-sm font-mono text-brand-light">{clickedNode}()</p>
                    <p className="text-xs text-[var(--text-muted)] mt-1">
                      Click a node in the graph, then ask about it in the chat.
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-[var(--text-muted)]">
                    Click a node in the Call graph tab to see details.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* right — agent status */}
        <div className="w-[200px] shrink-0 border-l border-[var(--border)] bg-[var(--bg-secondary)] overflow-y-auto">
          <AgentStatus lastIntent={lastIntent} />
        </div>

      </div>

      {showOnboarding && (
        <OnboardingModal
          onClose={() => setShowOnboarding(false)}
          onIndexed={(repo) => setCurrentRepo(repo)}
        />
      )}
    </div>
  );
}