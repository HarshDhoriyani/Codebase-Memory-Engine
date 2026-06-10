import tempfile
import subprocess
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..parser.walker import walk_repo, SKIP_DIRS
from ..parser.models import ParseResult, DependencyGraph
from ..parser.graph_builder import build_dependency_graph
from ..graph.inserter import store_graph
from ..graph.queries import (
    what_does_function_call,
    what_calls_function,
    full_call_chain,
    most_complex_functions,
    most_called_functions,
    graph_stats,
    what_imports_module,
)

router = APIRouter()

class IngestLocalRequest(BaseModel):
    repo_path: str

class IngestGithubRequest(BaseModel):
    github_url: str

class IngestResponse(BaseModel):
    total_files: int
    total_functions: int
    results: list[ParseResult]


@router.post("/ingest/local", response_model=IngestResponse)
async def ingest_local(req: IngestLocalRequest):
    results = await walk_repo(req.repo_path)
    total_fn = sum(len(r.functions) for r in results)
    return IngestResponse(
        total_files=len(results),
        total_functions=total_fn,
        results=results,
    )

@router.post("/ingest/github", response_model=IngestResponse)
async def ingest_github(req: IngestGithubRequest):
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            ["git", "clone", "--depth=1", req.github_url, tmp],
            capture_output=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=400, detail="Clone failed. Check the URL.")
        results = await walk_repo(tmp)
    
    total_fn = sum(len(r.functions) for r in results)
    return IngestResponse(
        total_files=len(results),
        total_functions=total_fn,
        results=results,
    )

@router.post("/analyze/graph", response_model=DependencyGraph)
async def analyze_graph(req: IngestGithubRequest):
    """
    Clone a repo, parse all files, then build the full dependency + call graph. Return nodes, edges, import map, and any circular dependencies detected.
    """
    with tempfile.TemporaryDirectory() as tmp:
        clone = subprocess.run(
            ["git", "clone", "--depth=1", req.github_url, tmp],
            capture_output=True,
            timeout=60,
        )
        if clone.returncode != 0:
            raise HTTPException(status_code=400, detail="Clone failed.")
        
        parse_results = await walk_repo(tmp)

        source_map: dict[str, str] = {}
        root = Path(tmp)
        for result in parse_results:
            full_path = root / result.file_path
            try:
                async with aiofiles.open(
                    full_path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    source_map[result.file_path] = await f.read()
            except Exception:
                pass

    graph = build_dependency_graph(parse_results, source_map)
    return graph

@router.post("/analyze/graph/summary")
async def analyze_graph_summary(req: IngestGithubRequest):
    """
    Same as /analyze/graph but returns only the summary - safe for Swagger UI.
    """
    with tempfile.TemporaryDirectory() as tmp:
        clone = subprocess.run(
            ["git", "clone", "--depth=1", req.github_url, tmp],
            capture_output=True, timeout=60,
        )

        if clone.returncode != 0:
            raise HTTPException(status_code=400, detail="Clone failed.")
        parse_results = await walk_repo(tmp)
        source_map = {}
        root = Path(tmp)
        for res in parse_results:
            full_path = root / res.file_path
            try:
                async with aiofiles.open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    source_map[res.file_path] = await f.read()
            except Exception:
                pass
        
    graph = build_dependency_graph(parse_results, source_map)
    return {
        "total_files": graph.total_files,
        "total_functions": graph.total_functions,
        "total_edges": graph.total_edges,
        "circular_dependencies": graph.circular_dependencies,
        "sample_edges": [
            {"caller": e.caller_name, "callee": e.callee_name, "line": e.call_line}
            for e in graph.edges[:10]
        ],
        "sample_imports": dict(list(graph.import_map.items())[:5]),
    }


@router.post("/graph/store")
async def store_repo_graph(req: IngestGithubRequest):
    with tempfile.TemporaryDirectory() as tmp:
        clone = subprocess.run(
            ["git", "clone", "--depth=1", req.github_url, tmp],
            capture_output=True, timeout=60,
        )

        if clone.returncode != 0:
            raise HTTPException(status_code=400, detail="Clone failed.")
        

        parse_results = await walk_repo(tmp)
        source_map = {}
        root = Path(tmp)
        for result in parse_results:
            full_path = root / result.file_path
            try:
                async with aiofiles.open(
                    full_path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    source_map[result.file_path] = await f.read()
            except Exception:
                pass

    graph = build_dependency_graph(parse_results, source_map)
    summary = store_graph(parse_results, graph)
    return {"status": "stored", **summary}


@router.get("/graph/stats")
async def get_graph_stats():
    return graph_stats()


@router.get("/graph/function/{name}/calls")
async def get_function_calls(name: str):
    return {"function": name, "calls": what_does_function_call(name)}

@router.get("/graph/function/{name}/called-by")
async def get_called_by(name: str):
    return {"function": name, "called_by": what_calls_function(name)}

@router.get("/graph/function/{name}/chain")
async def get_call_chain(name: str, depth: int = 5):
    return {"function": name, "chain": full_call_chain(name, depth)}

@router.get("/graph/most-complex")
async def get_most_complex(limit: int = 10):
    return {"functions": most_complex_functions(limit)}

@router.get("/graph/most-called")
async def get_most_called(limit: int = 10):
    return {"functions": most_called_functions(limit)}

@router.get("/graph/imports/{module_name}")
async def get_imports(module_name: str):
    return {"module": module_name, "imported_by": what_imports_module(module_name)}