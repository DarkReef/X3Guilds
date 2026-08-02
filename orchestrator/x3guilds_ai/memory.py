from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from x3guilds_ai.models import DialogueResponse, StoredMessage


class SQLiteMemoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    async def initialize(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, id);

                CREATE TABLE IF NOT EXISTS request_cache (
                    request_id TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    async def get_cached(self, request_id: str) -> DialogueResponse | None:
        async with self._lock:
            raw = await asyncio.to_thread(self._get_cached_sync, request_id)
        if raw is None:
            return None
        response = DialogueResponse.model_validate_json(raw)
        return response.model_copy(update={"cached": True})

    def _get_cached_sync(self, request_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response_json FROM request_cache WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return None if row is None else str(row["response_json"])

    async def append(self, conversation_id: str, message: StoredMessage) -> None:
        async with self._lock:
            await asyncio.to_thread(self._append_sync, conversation_id, message)

    def _append_sync(self, conversation_id: str, message: StoredMessage) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages(conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, message.role, message.content),
            )

    async def recent(self, conversation_id: str, limit: int) -> list[StoredMessage]:
        async with self._lock:
            rows = await asyncio.to_thread(self._recent_sync, conversation_id, limit)
        return [StoredMessage(role=row["role"], content=row["content"]) for row in rows]

    def _recent_sync(self, conversation_id: str, limit: int) -> list[sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return list(reversed(rows))

    async def cache(self, response: DialogueResponse) -> None:
        raw = response.model_dump_json()
        async with self._lock:
            await asyncio.to_thread(self._cache_sync, response.request_id, raw)

    def _cache_sync(self, request_id: str, raw: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO request_cache(request_id, response_json) VALUES (?, ?)",
                (request_id, raw),
            )
