from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    provider: str = "mock"
    database_path: Path = Path("./data/x3guilds-ai.sqlite3")
    gigachat_credentials: str | None = None
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-2"
    gigachat_base_url: str = "https://api.giga.chat"
    gigachat_oauth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    gigachat_verify_ssl: bool = True
    history_limit: int = 12

    @classmethod
    def from_env(cls) -> "Settings":
        history_limit = int(os.getenv("X3AI_HISTORY_LIMIT", "12"))
        if not 1 <= history_limit <= 50:
            raise ValueError("X3AI_HISTORY_LIMIT must be between 1 and 50")
        return cls(
            provider=os.getenv("X3AI_PROVIDER", "mock").strip().lower(),
            database_path=Path(os.getenv("X3AI_DATABASE_PATH", "./data/x3guilds-ai.sqlite3")),
            gigachat_credentials=os.getenv("X3AI_GIGACHAT_CREDENTIALS") or None,
            gigachat_scope=os.getenv("X3AI_GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
            gigachat_model=os.getenv("X3AI_GIGACHAT_MODEL", "GigaChat-2"),
            gigachat_base_url=os.getenv("X3AI_GIGACHAT_BASE_URL", "https://api.giga.chat").rstrip("/"),
            gigachat_oauth_url=os.getenv(
                "X3AI_GIGACHAT_OAUTH_URL",
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            ),
            gigachat_verify_ssl=_as_bool(os.getenv("X3AI_GIGACHAT_VERIFY_SSL"), True),
            history_limit=history_limit,
        )
