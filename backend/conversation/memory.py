import sqlite3
import uuid

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "conversations.db"


class ConversationMemory:

    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path

        Path(self.db_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.initialize_database()

    def get_connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize_database(self):

        with self.get_connection() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    repository_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY(session_id)
                    REFERENCES sessions(session_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_messages_session_repository

                ON messages(session_id, repository_id, id)
            """)

    def create_session(
        self,
        repository_id: str,
        session_id: Optional[str] = None
    ) -> str:

        if not repository_id:
            raise ValueError("Repository ID cannot be empty.")

        session_id = session_id or str(uuid.uuid4())

        with self.get_connection() as conn:

            existing = conn.execute("""
                SELECT repository_id
                FROM sessions
                WHERE session_id = ?
            """, (session_id,)).fetchone()

            if existing:
                if existing["repository_id"] != repository_id:
                    raise ValueError(
                        "Session already belongs to another repository."
                    )

                return session_id

            conn.execute("""
                INSERT INTO sessions (
                    session_id,
                    repository_id,
                    created_at
                )
                VALUES (?, ?, ?)
            """, (
                session_id,
                repository_id,
                datetime.now(timezone.utc).isoformat()
            ))

        return session_id

    def validate_session(
        self,
        session_id: str,
        repository_id: str
    ):

        with self.get_connection() as conn:

            session = conn.execute("""
                SELECT repository_id
                FROM sessions
                WHERE session_id = ?
            """, (session_id,)).fetchone()

        if not session:
            raise ValueError("Session does not exist.")

        if session["repository_id"] != repository_id:
            raise ValueError(
                "Session does not belong to this repository."
            )

    def save_message(
        self,
        session_id: str,
        repository_id: str,
        role: str,
        content: str
    ):

        if role not in ("user", "assistant"):
            raise ValueError("Role must be user or assistant.")

        if not content:
            raise ValueError("Message content cannot be empty.")

        self.validate_session(session_id, repository_id)

        with self.get_connection() as conn:

            conn.execute("""
                INSERT INTO messages (
                    session_id,
                    repository_id,
                    role,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                repository_id,
                role,
                content,
                datetime.now(timezone.utc).isoformat()
            ))

    def save_interaction(
        self,
        session_id: str,
        repository_id: str,
        question: str,
        answer: str
    ):

        self.validate_session(session_id, repository_id)

        timestamp = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as conn:

            conn.executemany("""
                INSERT INTO messages (
                    session_id,
                    repository_id,
                    role,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, [
                (
                    session_id,
                    repository_id,
                    "user",
                    question,
                    timestamp
                ),
                (
                    session_id,
                    repository_id,
                    "assistant",
                    answer,
                    timestamp
                )
            ])

    def get_history(
        self,
        session_id: str,
        repository_id: str,
        limit: int = 10
    ) -> List[Dict]:

        if limit < 1:
            raise ValueError("History limit must be positive.")

        self.validate_session(session_id, repository_id)

        with self.get_connection() as conn:

            rows = conn.execute("""
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                AND repository_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (
                session_id,
                repository_id,
                limit
            )).fetchall()

        # Reverse to restore chronological order.
        return [
            dict(row)
            for row in reversed(rows)
        ]

    def delete_session(
        self,
        session_id: str,
        repository_id: str
    ):

        self.validate_session(session_id, repository_id)

        with self.get_connection() as conn:

            conn.execute("""
                DELETE FROM messages
                WHERE session_id = ?
                AND repository_id = ?
            """, (session_id, repository_id))

            conn.execute("""
                DELETE FROM sessions
                WHERE session_id = ?
                AND repository_id = ?
            """, (session_id, repository_id))


if __name__ == "__main__":

    memory = ConversationMemory()

    repository_id = "sample_repository"

    session_id = memory.create_session(repository_id)

    memory.save_interaction(
        session_id=session_id,
        repository_id=repository_id,
        question="How does authentication work?",
        answer="Authentication is handled by the login controller."
    )

    memory.save_interaction(
        session_id=session_id,
        repository_id=repository_id,
        question="Where is the token verified?",
        answer="The authentication middleware verifies the token."
    )

    history = memory.get_history(
        session_id=session_id,
        repository_id=repository_id,
        limit=10
    )

    print("Session ID:", session_id)
    print("\nConversation History:")

    for message in history:
        print(f"{message['role']}: {message['content']}")