from fastembed import TextEmbedding
from functools import lru_cache
from ..parser.models import ParseResult

MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIM = 384

@lru_cache(maxsize=1)
def get_model() -> TextEmbedding:
    print(f"Loading embedding model: {MODEL_NAME}")
    return TextEmbedding(model_name=MODEL_NAME)


def build_function_text(fn: dict) -> str:
    """
    Build a rich natural-language description of a function.
    The richer this text, the better the semantic search.

    We combine: name + file + params + return type + docstring + body snippet.
    This gives the model enough context to understand what the function does,
    not just what it's called.
    """
    parts = [
        f"Function: {fn['name']}",
        f"File: {fn['file_path']}",
    ]

    if fn.get("params"):
        parts.append(f"Parameters: {', '.join(fn['params'][:5])}")

    if fn.get("return_type"):
        parts.append(f"Returns: {fn['return_type']}")

    if fn.get("docstring"):
        parts.append(f"Description: {fn['docstring'][:200]}")

    body = fn.get("body", "")
    if body:
        body_lines = body.split("\n")[1:9]
        snippet = " ".join(l.strip() for l in body_lines if l.strip())
        if snippet:
            parts.append(f"Code: {snippet[:300]}")
    
    return "\n".join(parts)

def embed_functions(parse_results: list[ParseResult]) -> list[dict]:
    model = get_model()

    all_fns = []
    for result in parse_results:
        for fn in result.functions:
            all_fns.append({
                "function_id": f"{fn.file_path}::{fn.name}::{fn.start_line}",
                "name": fn.name,
                "file_path": fn.file_path,
                "language": fn.language,
                "complexity": fn.complexity,
                "docstring": fn.docstring or "",
                "params": fn.params,
                "return_type": fn.return_type or "",
                "start_line": fn.start_line,
                "body": fn.body,
            })
    
    if not all_fns:
        return []
    
    print(f"Embedding {len(all_fns)} functions...")

    texts = [build_function_text(fn) for fn in all_fns]

    embeddings = list(model.embed(texts))

    result_list = []
    for fn, emb in zip(all_fns, embeddings):
        fn["vector"] = emb.tolist()
        del fn["body"]
        result_list.append(fn)

    print(f"Embedded {len(all_fns)} functions")
    return result_list

def embed_query(query: str) -> list[float]:
    model = get_model()
    embeddings = list(model.embed([query]))
    return embeddings[0].tolist()