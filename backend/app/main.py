from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .graph.schema import setup_schema
from .graph.client import is_connected as neo4j_connected
from .embedder.qdrant_store import setup_collection, is_connected as qdrant_connected
from .explainer.explainer import is_available

app = FastAPI(title="Codebase Memory Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    if neo4j_connected():
        setup_schema()
        print("Neo4j connected")
    else:
        print("Neo4j not available")

    if qdrant_connected():
        setup_collection()
        print("Qdrant Connected")
    else:
        print("Qdrant Not Available")

    if is_available():
        print("Groq API key found")
    else:
        print("GROQ_API_KEY not set - /explain endpoints disabled")


@app.get("/")
async def health():
    return {
        "status": "ok",
        "neo4j": neo4j_connected(),
        "qdrant": qdrant_connected(),
        "groq": is_available(),
    }