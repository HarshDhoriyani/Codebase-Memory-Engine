import os
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import lru_cache


def get_connection():
    url = os.getenv("POSTGRES_URL", "postgresql://cme:cme123@postgres:5432/cme")
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def is_connected() -> bool:
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False


def setup_tables():
    """Create tables if they don't exist."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS indexed_repos (
            id              SERIAL PRIMARY KEY,
            github_url      TEXT UNIQUE NOT NULL,
            repo_name       TEXT NOT NULL,
            last_commit     TEXT,
            indexed_at      TIMESTAMP DEFAULT NOW(),
            total_files     INTEGER DEFAULT 0,
            total_functions INTEGER DEFAULT 0,
            total_edges     INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'indexed'
        );

        CREATE TABLE IF NOT EXISTS indexed_files (
            id          SERIAL PRIMARY KEY,
            repo_id     INTEGER REFERENCES indexed_repos(id) ON DELETE CASCADE,
            file_path   TEXT NOT NULL,
            file_hash   TEXT NOT NULL,
            indexed_at  TIMESTAMP DEFAULT NOW(),
            UNIQUE(repo_id, file_path)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Postgres tables ready")