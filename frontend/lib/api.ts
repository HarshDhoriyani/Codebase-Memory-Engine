// proxy (for short requests through Next.js)
const PROXY = "/api/backend";

// direct (for long-running requests that would timeout through proxy)
const DIRECT = "http://localhost:8000/api/v1";

export interface QueryResponse {
  query:          string;
  intent:         string;
  confidence:     number;
  function_name:  string | null;
  context:        string;
  graph_data:     Record<string, unknown>;
  vector_results: unknown[];
  errors:         string[];
}

export interface ExplainResponse {
  query:        string;
  intent:       string;
  function:     string | null;
  answer:       string;
  context_used: string;
}

export interface GraphStats {
  files:     number;
  functions: number;
  modules:   number;
  calls:     number;
  imports:   number;
}

export interface FunctionNode {
  name:         string;
  file_path:    string;
  complexity?:  number;
  call_count?:  number;
  change_count?:number;
}

// ── health ────────────────────────────────────────────────

export async function fetchHealth() {
  const res = await fetch(`${DIRECT.replace("/api/v1", "")}/`);
  return res.json();
}

// ── ingest (direct — long running) ───────────────────────

export async function ingestRepo(githubUrl: string) {
  const res = await fetch(`${DIRECT}/graph/store`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ github_url: githubUrl }),
  });
  return res.json();
}

export async function embedRepo(githubUrl: string) {
  const res = await fetch(`${DIRECT}/search/embed`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ github_url: githubUrl }),
  });
  return res.json();
}

// ── graph queries (proxy — fast) ──────────────────────────

export async function fetchGraphStats(): Promise<GraphStats> {
  const res = await fetch(`${DIRECT}/graph/stats`);
  return res.json();
}

export async function fetchMostCalled(limit = 30): Promise<{ functions: FunctionNode[] }> {
  const res = await fetch(`${DIRECT}/graph/most-called?limit=${limit}`);
  return res.json();
}

export async function fetchFunctionCalls(name: string) {
  const res = await fetch(`${DIRECT}/graph/function/${encodeURIComponent(name)}/calls`);
  return res.json();
}

export async function fetchFunctionCalledBy(name: string) {
  const res = await fetch(`${DIRECT}/graph/function/${encodeURIComponent(name)}/called-by`);
  return res.json();
}

// ── explain (direct — streaming) ─────────────────────────

export async function explainFull(query: string): Promise<ExplainResponse> {
  const res = await fetch(`${DIRECT}/explain/full`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ query }),
  });
  return res.json();
}

export function explainStream(
  query: string,
  onMeta:  (meta: { intent: string; confidence: number; function?: string }) => void,
  onChunk: (chunk: string) => void,
  onDone:  () => void,
  onError: (err: string) => void,
): () => void {
  const controller = new AbortController();

  fetch(`${DIRECT}/explain`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ query }),
    signal:  controller.signal,
  }).then(async (res) => {
    const reader  = res.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const raw   = decoder.decode(value);
      const lines = raw.split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const payload = JSON.parse(line.slice(6));
          if (payload.type === "meta")  onMeta(payload);
          if (payload.type === "chunk") onChunk(payload.text);
          if (payload.type === "done")  onDone();
        } catch {}
      }
    }
  }).catch((err) => {
    if (err.name !== "AbortError") onError(String(err));
  });

  return () => controller.abort();
}

export async function ingestFull(githubUrl: string) {
  const res = await fetch(`${DIRECT}/ingest/full`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ github_url: githubUrl }),
  });
  return res.json();
}