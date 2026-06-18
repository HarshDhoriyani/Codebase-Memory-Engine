from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from functools import lru_cache
import os
import hashlib

COLLECTION_NAME = "functions"
VECTOR_SIZE = 384
BATCH_SIZE = 100

@lru_cache(maxsize=1)
def get_qdrant() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))

    print("=" * 50)
    print(f"QDRANT_HOST = {host}")
    print(f"QDRANT_PORT = {port}")
    print("=" * 50)
    
    return QdrantClient(host=host, port=port)


def setup_collection():
    client = get_qdrant()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print(f"Qdrant collection '{COLLECTION_NAME}' created")
    else:
        print(f"Qdrant collection '{COLLECTION_NAME}' ready")


def _stable_id(function_id: str) -> int:
    return int(hashlib.md5(function_id.encode()).hexdigest()[:15], 16)


def upsert_functions(functions_with_vectors: list[dict]) -> int:
    client = get_qdrant()

    points = [
        PointStruct(
            id = _stable_id(item["function_id"]),
            vector=item["vector"],
            payload={
                "function_id": item["function_id"],
                "name": item["name"],
                "file_path": item["file_path"],
                "language": item.get("language", ""),
                "complexity": item.get("complexity", 0),
                "docstring": item.get("docstring", ""),
                "params": item.get("params", []),
                "start_line": item.get("start_line", 0),
            },
        )
        for item in functions_with_vectors
    ]

    for i in range(0, len(points), BATCH_SIZE):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i:i + BATCH_SIZE],
        )

    return len(points)


def semantic_search(
        query_vector: list[float],
        limit: int=10,
        language_filter: str=None, # type: ignore
        min_score: float=0.3,
) -> list[dict]:
    
    client = get_qdrant()

    query_filter = None
    if language_filter:
        query_filter = Filter(
            must=[FieldCondition(
                key="language",
                match=MatchValue(value=language_filter),
            )]
        )

    results = client.search( # type: ignore
        collection_name = COLLECTION_NAME,
        query_vector=query_vector,
        limit = limit,
        query_filter = query_filter,
        with_payload = True,
        score_threshold = min_score,
    )

    return [
        {
            "score": round(r.score, 4),
            "name": r.payload.get("name"),
            "file_path": r.payload.get("file_path"),
            "function_id": r.payload.get("function_id"),
            "docstring": r.payload.get("docstring"),
            "complexity": r.payload.get("complexity"),
            "start_line": r.payload.get("start_line"),
            "params": r.payload.get("params"),
        }
        for r in results
    ]


def collection_stats() -> dict:
    client = get_qdrant()
    info = client.get_collection(COLLECTION_NAME)
    return {
        "total_vectors": info.points_count,
        "vector_size": VECTOR_SIZE,
        "collection": COLLECTION_NAME,
        "status": str(info.status),
    }


def is_connected() -> bool:
    try:
        get_qdrant().get_collections()
        return True
    except Exception:
        return False
    