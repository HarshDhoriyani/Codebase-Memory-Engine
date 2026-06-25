import hashlib
from pathlib import Path


def hash_file(content: str) -> str:
    """MD5 hash of file content — used to detect changes."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def compute_file_hashes(
    repo_path: str,
    parse_results: list,
) -> dict[str, str]:
    """
    Compute content hash for every parsed file.
    Returns {file_path: hash}
    """
    root   = Path(repo_path)
    hashes = {}

    for result in parse_results:
        full_path = root / result.file_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            hashes[result.file_path] = hash_file(content)
        except Exception:
            pass

    return hashes


def find_changed_files(
    old_hashes: dict[str, str],
    new_hashes: dict[str, str],
) -> dict[str, str]:
    """
    Compare old vs new file hashes.
    Returns only the files that changed or are new.

    old_hashes: {file_path: hash} from Postgres (previous index)
    new_hashes: {file_path: hash} from current clone
    """
    changed = {}

    for file_path, new_hash in new_hashes.items():
        old_hash = old_hashes.get(file_path)
        if old_hash != new_hash:
            changed[file_path] = new_hash

    deleted = set(old_hashes.keys()) - set(new_hashes.keys())

    return changed, deleted