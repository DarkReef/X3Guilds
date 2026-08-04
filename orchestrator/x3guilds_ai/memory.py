from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from x3guilds_ai.models import ChatRequest, DialogueResponse, StoredMessage


class RequestIdConflictError(RuntimeError):
    pass


class SQLiteMemoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
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

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(conversation_id, fact_key)
                );
                CREATE INDEX IF NOT EXISTS idx_memories_conversation
                    ON memories(conversation_id, id);

                CREATE TABLE IF NOT EXISTS request_cache (
                    request_id TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(request_cache)").fetchall()
            }
            if "request_fingerprint" not in columns:
                connection.execute(
                    "ALTER TABLE request_cache ADD COLUMN request_fingerprint TEXT NOT NULL DEFAULT ''"
                )

    async def get_cached(self, request: ChatRequest) -> DialogueResponse | None:
        async with self._lock:
            row = await asyncio.to_thread(self._get_cached_sync, request.request_id)
        if row is None:
            return None
        fingerprint = str(row["request_fingerprint"])
        if fingerprint and fingerprint != request.fingerprint():
            raise RequestIdConflictError(
                f"request_id {request.request_id!r} was already used for another payload"
            )
        response = DialogueResponse.model_validate_json(str(row["response_json"]))
        return response.model_copy(update={"cached": True})

    def _get_cached_sync(self, request_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT request_fingerprint, response_json FROM request_cache WHERE request_id = ?",
                (request_id,),
            ).fetchone()

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
                SELECT role, content FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return list(reversed(rows))

    async def add_memories(
        self,
        conversation_id: str,
        entity_id: str,
        facts: list[str],
    ) -> None:
        if not facts:
            return
        async with self._lock:
            await asyncio.to_thread(
                self._add_memories_sync,
                conversation_id,
                entity_id,
                facts,
            )

    def _add_memories_sync(
        self,
        conversation_id: str,
        entity_id: str,
        facts: list[str],
    ) -> None:
        with self._connect() as connection:
            for fact in facts:
                key = " ".join(fact.casefold().split())
                connection.execute(
                    """
                    INSERT OR IGNORE INTO memories(conversation_id, entity_id, fact, fact_key)
                    VALUES (?, ?, ?, ?)
                    """,
                    (conversation_id, entity_id, fact, key),
                )

    async def memories(self, conversation_id: str, limit: int) -> list[str]:
        async with self._lock:
            rows = await asyncio.to_thread(self._memories_sync, conversation_id, limit)
        return [str(row["fact"]) for row in rows]

    def _memories_sync(self, conversation_id: str, limit: int) -> list[sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT fact FROM memories
                WHERE conversation_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return list(reversed(rows))

    async def cache(self, request: ChatRequest, response: DialogueResponse) -> None:
        raw = response.model_dump_json()
        async with self._lock:
            await asyncio.to_thread(
                self._cache_sync,
                request.request_id,
                request.fingerprint(),
                raw,
            )

    def _cache_sync(self, request_id: str, fingerprint: str, raw: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO request_cache(
                    request_id, request_fingerprint, response_json
                ) VALUES (?, ?, ?)
                """,
                (request_id, fingerprint, raw),
            )
