import aiofiles
from pathlib import Path
from ..parser.ast_parser import parse_file
from ..parser.models import ParseResult
from ..graph.client import get_driver
from ..embedder.embedder import build_function_text, get_model
from ..embedder.qdrant_store import get_qdrant, COLLECTION_NAME, _stable_id
from qdrant_client.models import PointStruct


async def read_file(path: Path) -> str | None:
    try:
        async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
            return await f.read()
    except Exception:
        return None


async def reindex_changed_files(
    repo_path: str,
    changed_files: dict[str, str],   # file_path → new hash
    deleted_files: set[str],
) -> dict:
    """
    Incrementally update Neo4j and Qdrant for only the changed files.
    Returns summary of what was updated.
    """
    root    = Path(repo_path)
    updated = 0
    deleted = 0

    driver  = get_driver()
    qdrant  = get_qdrant()
    model   = get_model()

    # ── step 1: handle deleted files ─────────────────────
    if deleted_files:
        with driver.session() as session:
            session.run("""
                UNWIND $paths AS path
                MATCH (f:File {path: path})
                DETACH DELETE f
            """, {"paths": list(deleted_files)})

        # also remove their vectors from Qdrant
        for file_path in deleted_files:
            try:
                qdrant.delete(
                    collection_name=COLLECTION_NAME,
                    points_selector={"filter": {
                        "must": [{"key": "file_path", "match": {"value": file_path}}]
                    }},
                )
            except Exception:
                pass
        deleted = len(deleted_files)

    # ── step 2: re-parse + re-index changed files ─────────
    for file_path in changed_files:
        full_path = root / file_path
        source    = await read_file(full_path)
        if not source:
            continue

        result: ParseResult = parse_file(file_path, source)
        if not result.functions:
            continue

        # update Neo4j — remove old nodes for this file, insert new ones
        with driver.session() as session:
            session.run("""
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[:DEFINES]->(fn:Function)
                DETACH DELETE fn, f
            """, {"path": file_path})

            # re-insert file + functions
            session.run("""
                MERGE (f:File {path: $path})
                SET f.language = $language
            """, {"path": file_path, "language": result.language})

            for fn in result.functions:
                fid = f"{fn.file_path}::{fn.name}::{fn.start_line}"
                session.run("""
                    MATCH (f:File {path: $file_path})
                    MERGE (fn:Function {id: $id})
                    SET fn.name       = $name,
                        fn.file_path  = $file_path,
                        fn.complexity = $complexity,
                        fn.start_line = $start_line,
                        fn.end_line   = $end_line,
                        fn.docstring  = $docstring
                    MERGE (f)-[:DEFINES]->(fn)
                """, {
                    "id":         fid,
                    "file_path":  fn.file_path,
                    "name":       fn.name,
                    "complexity": fn.complexity,
                    "start_line": fn.start_line,
                    "end_line":   fn.end_line,
                    "docstring":  fn.docstring or "",
                })

        # re-embed functions for this file
        fn_dicts = [
            {
                "function_id": f"{fn.file_path}::{fn.name}::{fn.start_line}",
                "name":        fn.name,
                "file_path":   fn.file_path,
                "language":    fn.language,
                "complexity":  fn.complexity,
                "docstring":   fn.docstring or "",
                "params":      fn.params,
                "return_type": fn.return_type or "",
                "start_line":  fn.start_line,
                "body":        fn.body,
            }
            for fn in result.functions
        ]

        texts      = [build_function_text(d) for d in fn_dicts]
        embeddings = list(model.embed(texts))

        points = [
            PointStruct(
                id=_stable_id(d["function_id"]),
                vector=emb.tolist(),
                payload={
                    "function_id": d["function_id"],
                    "name":        d["name"],
                    "file_path":   d["file_path"],
                    "language":    d.get("language", ""),
                    "complexity":  d.get("complexity", 0),
                    "docstring":   d.get("docstring", ""),
                    "start_line":  d.get("start_line", 0),
                },
            )
            for d, emb in zip(fn_dicts, embeddings)
        ]

        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        updated += 1

    return {
        "files_updated": updated,
        "files_deleted": deleted,
    }