import asyncio
from pathlib import Path
import aiofiles
from .ast_parser import parse_file, detect_language
from .models import ParseResult

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".next", "coverage", ".mypy_cache", ".pytest_cache", "target", "vendor",
}

MAX_FILE_SIZE_BYTES = 500_000

async def read_file_safe(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return None
        async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
            return await f.read()
    except Exception:
        return None
    
async def walk_repo(repo_path: str) -> list[ParseResult]: # type: ignore
    root = Path(repo_path)
    tasks = []

    for file_path in root.rglob("*"):
        if any(part in SKIP_DIRS or part.startswith(".") # type: ignore
               for part in file_path.parts):
            continue
        if not file_path.is_file():
            continue
        if not detect_language(str(file_path)):
            continue
        tasks.append(_parse_one(file_path, root))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, ParseResult)]

async def _parse_one(file_path: Path, root: Path) -> ParseResult | None:
    source = await read_file_safe(file_path)
    if source is None:
        return None
    
    rel_path = str(file_path.relative_to(root))
    return parse_file(rel_path, source)