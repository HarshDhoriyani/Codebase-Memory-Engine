from datetime import datetime
from .client import get_connection


def save_repo(
    github_url: str,
    last_commit: str,
    total_files: int,
    total_functions: int,
    total_edges: int,
) -> int:
    """Save or update repo metadata. Returns repo id."""
    conn = get_connection()
    cur  = conn.cursor()

    repo_name = github_url.rstrip("/").split("/")[-2] + "/" + github_url.rstrip("/").split("/")[-1]

    cur.execute("""
        INSERT INTO indexed_repos
            (github_url, repo_name, last_commit, total_files, total_functions, total_edges, indexed_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (github_url) DO UPDATE SET
            last_commit      = EXCLUDED.last_commit,
            total_files      = EXCLUDED.total_files,
            total_functions  = EXCLUDED.total_functions,
            total_edges      = EXCLUDED.total_edges,
            indexed_at       = NOW(),
            status           = 'indexed'
        RETURNING id
    """, (github_url, repo_name, last_commit, total_files, total_functions, total_edges))

    repo_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return repo_id


def save_file_hashes(repo_id: int, file_hashes: dict[str, str]):
    """Save file path → hash mapping for incremental diff detection."""
    conn = get_connection()
    cur  = conn.cursor()

    for file_path, file_hash in file_hashes.items():
        cur.execute("""
            INSERT INTO indexed_files (repo_id, file_path, file_hash, indexed_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (repo_id, file_path) DO UPDATE SET
                file_hash  = EXCLUDED.file_hash,
                indexed_at = NOW()
        """, (repo_id, file_path, file_hash))

    conn.commit()
    cur.close()
    conn.close()


def get_repo(github_url: str) -> dict | None:
    """Get repo metadata if previously indexed."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT * FROM indexed_repos WHERE github_url = %s",
        (github_url,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def get_file_hashes(repo_id: int) -> dict[str, str]:
    """Get all stored file hashes for a repo."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT file_path, file_hash FROM indexed_files WHERE repo_id = %s",
        (repo_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r["file_path"]: r["file_hash"] for r in rows}


def list_repos() -> list[dict]:
    """List all indexed repos with metadata."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            github_url, repo_name, last_commit,
            indexed_at, total_files, total_functions,
            total_edges, status
        FROM indexed_repos
        ORDER BY indexed_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def delete_repo(github_url: str):
    """Remove repo from tracking."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM indexed_repos WHERE github_url = %s", (github_url,))
    conn.commit()
    cur.close()
    conn.close()