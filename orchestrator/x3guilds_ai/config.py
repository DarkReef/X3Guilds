from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int, minimum: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    provider: str = "mock"
    database_path: Path = Path("./data/x3guilds-ai.sqlite3")
    request_log_path: Path | None = None
    response_log_path: Path = Path("./data/x3guilds-ai-responses.log")
    checkpoint_path: Path = Path("./data/x3guilds-ai.checkpoint.json")
    diagnostics_path: Path = Path("./data/diagnostics")
    poll_interval_ms: int = 350
    overlay_enabled: bool = True
    overlay_always_on_top: bool = True
    overlay_width: int = 620
    overlay_height: int = 420
    gigachat_credentials: str | None = None
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-2"
    gigachat_base_url: str = "https://api.giga.chat"
    gigachat_oauth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    gigachat_verify_ssl: bool = True
    gigachat_timeout_seconds: float = 45.0
    gigachat_retries: int = 2
    history_limit: int = 12
    memory_limit: int = 20

    @classmethod
    def from_env(cls) -> "Settings":
        request_path = os.getenv("X3AI_REQUEST_LOG_PATH")
        return cls(
            provider=os.getenv("X3AI_PROVIDER", "mock").strip().lower(),
            database_path=Path(os.getenv("X3AI_DATABASE_PATH", "./data/x3guilds-ai.sqlite3")),
            request_log_path=Path(request_path) if request_path else None,
            response_log_path=Path(
                os.getenv("X3AI_RESPONSE_LOG_PATH", "./data/x3guilds-ai-responses.log")
            ),
            checkpoint_path=Path(
                os.getenv("X3AI_CHECKPOINT_PATH", "./data/x3guilds-ai.checkpoint.json")
            ),
            diagnostics_path=Path(os.getenv("X3AI_DIAGNOSTICS_PATH", "./data/diagnostics")),
            poll_interval_ms=_as_int("X3AI_POLL_INTERVAL_MS", 350, 50, 10_000),
            overlay_enabled=_as_bool(os.getenv("X3AI_OVERLAY_ENABLED"), True),
            overlay_always_on_top=_as_bool(os.getenv("X3AI_OVERLAY_ALWAYS_ON_TOP"), True),
            overlay_width=_as_int("X3AI_OVERLAY_WIDTH", 620, 320, 2400),
            overlay_height=_as_int("X3AI_OVERLAY_HEIGHT", 420, 240, 1600),
            gigachat_credentials=os.getenv("X3AI_GIGACHAT_CREDENTIALS") or None,
            gigachat_scope=os.getenv("X3AI_GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
            gigachat_model=os.getenv("X3AI_GIGACHAT_MODEL", "GigaChat-2"),
            gigachat_base_url=os.getenv("X3AI_GIGACHAT_BASE_URL", "https://api.giga.chat").rstrip("/"),
            gigachat_oauth_url=os.getenv(
                "X3AI_GIGACHAT_OAUTH_URL",
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            ),
            gigachat_verify_ssl=_as_bool(os.getenv("X3AI_GIGACHAT_VERIFY_SSL"), True),
            gigachat_timeout_seconds=float(os.getenv("X3AI_GIGACHAT_TIMEOUT_SECONDS", "45")),
            gigachat_retries=_as_int("X3AI_GIGACHAT_RETRIES", 2, 0, 5),
            history_limit=_as_int("X3AI_HISTORY_LIMIT", 12, 1, 50),
            memory_limit=_as_int("X3AI_MEMORY_LIMIT", 20, 1, 100),
        )
