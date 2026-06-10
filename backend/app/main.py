from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .graph.schema import setup_schema
from .graph.client import is_connected

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
    if is_connected():
        setup_schema()
        print("Neo4j Connected")
    else:
        print("Neo4j Not Available - graph features disabled")


@app.get("/")
async def health():
    return {
        "status": "ok",
        "neo4j": is_connected(),
    }