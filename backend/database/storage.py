import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
from config import METADATA_DB_PATH


class RepositoryStorage:
    def __init__(self, db_path: str = str(METADATA_DB_PATH)):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    repository_id TEXT PRIMARY KEY,
                    repository_name TEXT NOT NULL,
                    repository_url TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    status TEXT NOT NULL, -- 'cloning', 'indexing', 'ready', 'failed'
                    total_files INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    languages TEXT DEFAULT '[]', -- JSON string of detected languages
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    indexed_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS repository_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    FOREIGN KEY (repository_id) REFERENCES repositories(repository_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_repo_files_repo_id
                ON repository_files(repository_id)
            """)

    def create_repository(
        self,
        repository_id: str,
        repository_name: str,
        repository_url: str,
        local_path: str,
        status: str = "cloning"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO repositories (
                    repository_id, repository_name, repository_url, local_path, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (repository_id, repository_name, repository_url, local_path, status, now))
        return self.get_repository(repository_id)

    def update_status(
        self,
        repository_id: str,
        status: str,
        error_message: Optional[str] = None,
        total_files: Optional[int] = None,
        total_chunks: Optional[int] = None,
        languages: Optional[List[str]] = None
    ) -> None:
        updates = ["status = ?"]
        params: List[Any] = [status]

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if total_files is not None:
            updates.append("total_files = ?")
            params.append(total_files)

        if total_chunks is not None:
            updates.append("total_chunks = ?")
            params.append(total_chunks)

        if languages is not None:
            updates.append("languages = ?")
            params.append(json.dumps(languages))

        if status == "ready":
            updates.append("indexed_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

        params.append(repository_id)

        query = f"UPDATE repositories SET {', '.join(updates)} WHERE repository_id = ?"
        with self._get_connection() as conn:
            conn.execute(query, tuple(params))

    def save_indexed_files(
        self,
        repository_id: str,
        files_info: List[Dict[str, Any]]
    ) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM repository_files WHERE repository_id = ?", (repository_id,))
            conn.executemany("""
                INSERT INTO repository_files (repository_id, file_path, language, chunk_count)
                VALUES (?, ?, ?, ?)
            """, [
                (repository_id, f.get("file_path", ""), f.get("language", ""), f.get("chunk_count", 0))
                for f in files_info
            ])

    def get_repository(self, repository_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM repositories WHERE repository_id = ?
            """, (repository_id,)).fetchone()
            if not row:
                return None
            repo = dict(row)
            try:
                repo["languages"] = json.loads(repo.get("languages") or "[]")
            except Exception:
                repo["languages"] = []
            return repo

    def get_repository_by_url(self, repository_url: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM repositories WHERE repository_url = ?
            """, (repository_url,)).fetchone()
            if not row:
                return None
            repo = dict(row)
            try:
                repo["languages"] = json.loads(repo.get("languages") or "[]")
            except Exception:
                repo["languages"] = []
            return repo

    def list_repositories(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM repositories ORDER BY created_at DESC
            """).fetchall()
            results = []
            for r in rows:
                repo = dict(r)
                try:
                    repo["languages"] = json.loads(repo.get("languages") or "[]")
                except Exception:
                    repo["languages"] = []
                results.append(repo)
            return results

    def delete_repository(self, repository_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM repository_files WHERE repository_id = ?", (repository_id,))
            conn.execute("DELETE FROM repositories WHERE repository_id = ?", (repository_id,))
