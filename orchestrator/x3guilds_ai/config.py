from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


CONFIG_FILE_NAME = "x3guilds-ai.ini"


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, value: str | None, default: int, minimum: int, maximum: int) -> int:
    parsed = int(value) if value is not None and value.strip() else default
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _as_float(name: str, value: str | None, default: float, minimum: float, maximum: float) -> float:
    parsed = float(value) if value is not None and value.strip() else default
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def candidate_config_paths() -> list[Path]:
    paths: list[Path] = []
    configured = os.getenv("X3AI_CONFIG_PATH")
    if configured:
        paths.append(Path(configured).expanduser())

    paths.append(Path.cwd() / CONFIG_FILE_NAME)
    paths.append(Path(__file__).resolve().parents[1] / CONFIG_FILE_NAME)

    for variable in ("LOCALAPPDATA", "APPDATA"):
        root = os.getenv(variable)
        if root:
            paths.append(Path(root) / "X3GuildsAI" / CONFIG_FILE_NAME)

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = str(path.resolve(strict=False)).casefold()
        if normalized not in seen:
            unique.append(path)
            seen.add(normalized)
    return unique


def detect_config_path(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit.expanduser()
    for path in candidate_config_paths():
        if path.is_file():
            return path
    return None


def _read_config(path: Path | None) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    if path is not None:
        with path.open("r", encoding="utf-8-sig") as handle:
            parser.read_file(handle)
    return parser


def _resolve_path(raw: str, base_dir: Path) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve(strict=False)


@dataclass(frozen=True, slots=True)
class Settings:
    config_path: Path | None = None
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
    api_password: str | None = None

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        selected = detect_config_path(config_path)
        parser = _read_config(selected)
        base_dir = selected.parent if selected is not None else Path.cwd()

        def value(
            env_name: str,
            section: str,
            key: str,
            default: str | None = None,
        ) -> str | None:
            env_value = os.getenv(env_name)
            if env_value is not None:
                return env_value
            if parser.has_option(section, key):
                return parser.get(section, key)
            return default

        def path_value(
            env_name: str,
            section: str,
            key: str,
            default: str | None,
        ) -> Path | None:
            raw = value(env_name, section, key, default)
            if raw is None or not raw.strip():
                return None
            return _resolve_path(raw.strip(), base_dir)

        provider = (value("X3AI_PROVIDER", "general", "provider", "mock") or "mock").strip().lower()
        if provider not in {"mock", "gigachat"}:
            raise ValueError("provider must be 'mock' or 'gigachat'")

        credentials = value("X3AI_GIGACHAT_CREDENTIALS", "gigachat", "credentials")
        api_password = value("X3AI_API_PASSWORD", "security", "api_password")

        return cls(
            config_path=selected,
            provider=provider,
            database_path=path_value(
                "X3AI_DATABASE_PATH",
                "paths",
                "database",
                "data/x3guilds-ai.sqlite3",
            )
            or base_dir / "data/x3guilds-ai.sqlite3",
            request_log_path=path_value(
                "X3AI_REQUEST_LOG_PATH",
                "paths",
                "request_log",
                None,
            ),
            response_log_path=path_value(
                "X3AI_RESPONSE_LOG_PATH",
                "paths",
                "response_log",
                "data/x3guilds-ai-responses.log",
            )
            or base_dir / "data/x3guilds-ai-responses.log",
            checkpoint_path=path_value(
                "X3AI_CHECKPOINT_PATH",
                "paths",
                "checkpoint",
                "data/x3guilds-ai.checkpoint.json",
            )
            or base_dir / "data/x3guilds-ai.checkpoint.json",
            diagnostics_path=path_value(
                "X3AI_DIAGNOSTICS_PATH",
                "paths",
                "diagnostics",
                "data/diagnostics",
            )
            or base_dir / "data/diagnostics",
            poll_interval_ms=_as_int(
                "poll_interval_ms",
                value("X3AI_POLL_INTERVAL_MS", "general", "poll_interval_ms"),
                350,
                50,
                10_000,
            ),
            overlay_enabled=_as_bool(
                value("X3AI_OVERLAY_ENABLED", "overlay", "enabled"),
                True,
            ),
            overlay_always_on_top=_as_bool(
                value("X3AI_OVERLAY_ALWAYS_ON_TOP", "overlay", "always_on_top"),
                True,
            ),
            overlay_width=_as_int(
                "overlay_width",
                value("X3AI_OVERLAY_WIDTH", "overlay", "width"),
                620,
                320,
                2400,
            ),
            overlay_height=_as_int(
                "overlay_height",
                value("X3AI_OVERLAY_HEIGHT", "overlay", "height"),
                420,
                240,
                1600,
            ),
            gigachat_credentials=credentials.strip() if credentials and credentials.strip() else None,
            gigachat_scope=(
                value("X3AI_GIGACHAT_SCOPE", "gigachat", "scope", "GIGACHAT_API_PERS")
                or "GIGACHAT_API_PERS"
            ).strip(),
            gigachat_model=(
                value("X3AI_GIGACHAT_MODEL", "gigachat", "model", "GigaChat-2")
                or "GigaChat-2"
            ).strip(),
            gigachat_base_url=(
                value("X3AI_GIGACHAT_BASE_URL", "gigachat", "base_url", "https://api.giga.chat")
                or "https://api.giga.chat"
            ).rstrip("/"),
            gigachat_oauth_url=(
                value(
                    "X3AI_GIGACHAT_OAUTH_URL",
                    "gigachat",
                    "oauth_url",
                    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                )
                or "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            ).strip(),
            gigachat_verify_ssl=_as_bool(
                value("X3AI_GIGACHAT_VERIFY_SSL", "gigachat", "verify_ssl"),
                True,
            ),
            gigachat_timeout_seconds=_as_float(
                "gigachat_timeout_seconds",
                value("X3AI_GIGACHAT_TIMEOUT_SECONDS", "gigachat", "timeout_seconds"),
                45.0,
                1.0,
                300.0,
            ),
            gigachat_retries=_as_int(
                "gigachat_retries",
                value("X3AI_GIGACHAT_RETRIES", "gigachat", "retries"),
                2,
                0,
                5,
            ),
            history_limit=_as_int(
                "history_limit",
                value("X3AI_HISTORY_LIMIT", "memory", "history_limit"),
                12,
                1,
                50,
            ),
            memory_limit=_as_int(
                "memory_limit",
                value("X3AI_MEMORY_LIMIT", "memory", "memory_limit"),
                20,
                1,
                100,
            ),
            api_password=api_password.strip() if api_password and api_password.strip() else None,
        )

    @classmethod
    def from_env(cls) -> "Settings":
        """Backward-compatible alias. Environment variables override the INI file."""
        return cls.load()
