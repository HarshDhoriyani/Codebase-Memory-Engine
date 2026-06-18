# 🧠 Codebase Memory Engine

> Ask questions about any codebase in plain English. Understand its structure, its history, and its intent — without reading a single file.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Neo4j](https://img.shields.io/badge/Neo4j-5-blue?logo=neo4j)](https://neo4j.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-latest-red)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What is this?

Imagine you join a new company with 200,000 lines of code written over 4 years by 30 different people. Normally you'd spend weeks reading files and asking colleagues. **Codebase Memory Engine** gives you a conversational AI that already knows everything — and can explain any part of it in seconds.

It indexes an entire codebase — its structure, call relationships, import dependencies, and full git history — and makes all of it queryable in plain English.

```
"What functions does the routing module call?"
"Find all functions that handle authentication"
"Why has __init__ changed 47 times?"
"Which function has the most complex dependency graph?"
```

---

## Demo

Point it at the FastAPI repo itself:

```bash
# 1. ingest the repo
POST /api/v1/graph/store
{ "github_url": "https://github.com/fastapi/fastapi" }

# result: 1,124 files · 4,590 functions · 3,800+ call edges indexed in ~60s

# 2. semantic search — no keyword matching, pure meaning
POST /api/v1/search/semantic
{ "query": "functions that handle HTTP routing" }

# returns: add_api_route, include_router, setup_middleware — score 0.84

# 3. archaeology — trace the full history of a function
GET /api/v1/graph/function/__init__/history

# returns: changed 47 times · 3 authors · mostly feature additions
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Next.js Frontend                      │
│              Chat UI · Graph Viewer · Code View           │
└─────────────────────┬────────────────────────────────────┘
                       │ REST + SSE
┌─────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ AST Parser  │  │ Git Archaeo. │  │  Query Router   │ │
│  │ tree-sitter │  │  GitPython   │  │  LangGraph      │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘ │
│         │                │                    │          │
│  ┌──────▼──────┐  ┌──────▼───────┐  ┌────────▼────────┐ │
│  │  Call Graph │  │  Embedder    │  │  LLM Explainer  │ │
│  │  Dep. Map   │  │  fastembed   │  │   Claude API    │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────────────┘ │
└─────────┼────────────────┼──────────────────────────────┘
          │                │
   ┌──────▼──────┐  ┌──────▼───────┐  ┌──────────────────┐
   │    Neo4j    │  │    Qdrant    │  │      Redis       │
   │ Graph DB    │  │  Vector DB   │  │   Cache + Queue  │
   │ Cypher      │  │  Embeddings  │  │                  │
   └─────────────┘  └──────────────┘  └──────────────────┘
```

**Two pipelines:**

**Ingestion** (runs once per repo) — AST parse → call graph → Neo4j → embed → Qdrant → git mine → enrich

**Query** (runs on every question) — intent classify → route to graph/vectors/git → fuse context → LLM explain → stream answer

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AST Parsing | `tree-sitter` | Real grammar parser — handles nested functions, decorators, edge cases that regex can't |
| Graph DB | `Neo4j` + Cypher | Relationships are first-class — `MATCH (f)-[:CALLS*5]->(g)` in one query vs recursive SQL |
| Vector DB | `Qdrant` | Rust-native, 5x faster than FAISS. Cosine similarity for semantic search |
| Embeddings | `BAAI/bge-small-en-v1.5` | 23MB, runs locally, code-aware semantic understanding |
| Git Mining | `GitPython` | Programmatic access to full git object model — commits, diffs, blame |
| Backend | `FastAPI` + `asyncio` | Concurrent file parsing — 1,000 files in the same time as 100 |
| LLM | `Claude API` | Streaming, grounded answers with source attribution |
| Frontend | `Next.js 14` | Cytoscape.js graph visualizer + Monaco code viewer |
| Infra | `Docker Compose` | One command startup for all 4 services |

---

## Project Structure

```
codebase-memory-engine/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + startup
│   │   ├── parser/
│   │   │   ├── ast_parser.py       # tree-sitter AST extraction
│   │   │   ├── walker.py           # async recursive file walker
│   │   │   ├── import_extractor.py # import graph mining
│   │   │   ├── call_extractor.py   # call graph extraction
│   │   │   ├── graph_builder.py    # fuse into DependencyGraph
│   │   │   └── models.py           # Pydantic data models
│   │   ├── graph/
│   │   │   ├── client.py           # Neo4j connection
│   │   │   ├── schema.py           # constraints + indexes
│   │   │   ├── inserter.py         # bulk insert nodes/edges
│   │   │   └── queries.py          # Cypher query functions
│   │   ├── git/
│   │   │   ├── archaeologist.py    # mine commit history per function
│   │   │   └── classifier.py       # categorise commit messages
│   │   ├── embedder/
│   │   │   ├── embedder.py         # build text + embed functions
│   │   │   └── qdrant_store.py     # Qdrant collection management
│   │   └── api/
│   │       └── routes.py           # all API endpoints
│   ├── tests/
│   │   ├── test_parser.py
│   │   ├── test_call_graph.py
│   │   ├── test_graph.py
│   │   ├── test_git.py
│   │   └── test_embedder.py
│   ├── pytest.ini
│   ├── conftest.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                       # Next.js — coming in week 8
├── docker-compose.yml
├── .env
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- Git installed
- 4GB free RAM (Neo4j + Qdrant are memory hungry)

### 1. Clone the repo

```bash
git clone https://github.com/HarshDhoriyani/codebase-memory-engine
cd codebase-memory-engine
```

### 2. Set up environment

```bash
cp .env.example .env
# .env values are pre-filled for local Docker — no changes needed
```

### 3. Start all services

```bash
docker-compose up --build
```

Wait for all four lines:
```
✅ Neo4j connected
✅ Neo4j schema ready
✅ Qdrant connected
✅ Qdrant collection 'functions' created
INFO: Application startup complete.
```

### 4. Open the API

```
http://localhost:8000/docs    ← Swagger UI
http://localhost:7474         ← Neo4j browser (neo4j / password123)
```

---

## API Reference

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/github` | Parse all source files in a GitHub repo |
| `POST` | `/api/v1/ingest/local` | Parse a local repo by path |
| `POST` | `/api/v1/graph/store` | Parse + build + store full graph in Neo4j |
| `POST` | `/api/v1/git/enrich` | Mine git history and enrich Neo4j nodes |
| `POST` | `/api/v1/search/embed` | Embed all functions and store in Qdrant |

### Graph Queries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/graph/stats` | Node and edge counts in Neo4j |
| `GET` | `/api/v1/graph/most-complex` | Top functions by cyclomatic complexity |
| `GET` | `/api/v1/graph/most-called` | Most frequently called functions |
| `GET` | `/api/v1/graph/most-changed` | Most frequently git-modified functions |
| `GET` | `/api/v1/graph/function/{name}/calls` | What a function directly calls |
| `GET` | `/api/v1/graph/function/{name}/called-by` | What calls a function |
| `GET` | `/api/v1/graph/function/{name}/chain` | Full call chain (up to N hops) |
| `GET` | `/api/v1/graph/function/{name}/history` | Git provenance for a function |
| `GET` | `/api/v1/graph/imports/{module}` | Files that import a module |
| `GET` | `/api/v1/graph/category/{category}` | Functions by commit category |

### Semantic Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/search/semantic` | Find functions by meaning |
| `GET` | `/api/v1/search/stats` | Qdrant collection stats |

### Search request body

```json
{
  "query": "functions that validate user input",
  "limit": 10,
  "language": "python",
  "min_score": 0.3
}
```

---

## Example Queries

### Index a repo end-to-end

```bash
# Windows PowerShell
$base = "http://localhost:8000/api/v1"
$repo = '{"github_url": "https://github.com/fastapi/fastapi"}'

# 1. parse + store graph
Invoke-RestMethod -Method POST -Uri "$base/graph/store" -ContentType "application/json" -Body $repo

# 2. embed for semantic search
Invoke-RestMethod -Method POST -Uri "$base/search/embed" -ContentType "application/json" -Body $repo

# 3. enrich with git history
Invoke-RestMethod -Method POST -Uri "$base/git/enrich" -ContentType "application/json" -Body $repo
```

### Query the graph

```bash
# what is the most called function?
Invoke-RestMethod "$base/graph/most-called"

# full call chain from 'get' (5 hops deep)
Invoke-RestMethod "$base/graph/function/get/chain?depth=5"

# why did __init__ change so many times?
Invoke-RestMethod "$base/graph/function/__init__/history"

# semantic search
Invoke-RestMethod -Method POST -Uri "$base/search/semantic" `
  -ContentType "application/json" `
  -Body '{"query": "handle authentication and validate tokens", "limit": 5}'
```

### Neo4j Cypher (run at http://localhost:7474)

```cypher
// visualise the call graph
MATCH (f:Function)-[:CALLS]->(g:Function)
RETURN f, g LIMIT 50

// find functions that reach 'add_api_route' within 5 hops
MATCH path = (start:Function)-[:CALLS*1..5]->(end:Function {name: "add_api_route"})
RETURN DISTINCT start.name, start.file_path, length(path) AS hops
ORDER BY hops

// most changed bugfix functions
MATCH (f:Function)
WHERE f.primary_category = 'bugfix' AND f.change_count > 5
RETURN f.name, f.file_path, f.change_count, f.total_authors
ORDER BY f.change_count DESC
LIMIT 20
```

---

## Running Tests

```bash
# run all tests
docker-compose exec backend pytest tests/ -v

# run specific week
docker-compose exec backend pytest tests/test_parser.py -v
docker-compose exec backend pytest tests/test_call_graph.py -v
docker-compose exec backend pytest tests/test_git.py -v
docker-compose exec backend pytest tests/test_embedder.py -v
```

Current test coverage: **22 tests, all passing**

---

## Build Progress

| Week | Feature | Status |
|------|---------|--------|
| 1 | AST parser — tree-sitter, function extraction | ✅ Done |
| 2 | Call graph + import graph + cycle detection | ✅ Done |
| 3 | Neo4j graph DB — store nodes, edges, schema | ✅ Done |
| 4 | Git archaeologist — commit history per function | ✅ Done |
| 5 | Semantic embeddings — Qdrant + fastembed | ✅ Done |
| 6 | Query orchestrator — intent routing + context fusion | 🔨 Building |
| 7 | LLM explainer — Claude API + streaming + citations | ⬜ Planned |
| 8 | Next.js frontend — chat UI + graph visualiser | ⬜ Planned |
| 9 | GitHub integration — webhooks + incremental updates | ⬜ Planned |
| 10 | Deploy — Docker + CI/CD + Vercel + Fly.io | ⬜ Planned |

---

## Key Design Decisions

**Why Neo4j instead of Postgres for relationships?**
Finding all functions that call function X through N levels of nesting requires recursive CTEs in SQL — expensive to write and slow to execute. In Cypher: `MATCH (f)-[:CALLS*]->(g {name:'X'}) RETURN f` — one line, instant.

**Why tree-sitter instead of regex?**
tree-sitter builds a real AST and understands language grammar. It handles nested functions, decorators, async functions, and edge cases that regex-based approaches break on. Used by GitHub, Neovim, and Helix for the same reason.

**Why fastembed + local model instead of OpenAI embeddings?**
`BAAI/bge-small-en-v1.5` runs entirely in Docker — no API key, no cost, no rate limits, no data leaving the machine. At 23MB it's fast to download and produces 384-dimensional vectors that are strong for code similarity tasks.

**Why asyncio.gather() in the file walker?**
Parsing 1,000 files sequentially takes 10x longer than parsing them concurrently. `asyncio.gather()` dispatches all file reads in parallel — the bottleneck becomes disk I/O, not Python execution.

---

## Environment Variables

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
QDRANT_HOST=qdrant
QDRANT_PORT=6333
REDIS_URL=redis://redis:6379
```

All values are local Docker defaults — no external accounts needed for development.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run `docker-compose exec backend pytest tests/ -v` — all must pass
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

Harsh Dhoriyani