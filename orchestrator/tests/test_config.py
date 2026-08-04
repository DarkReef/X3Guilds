from pathlib import Path

from x3guilds_ai.config import Settings, detect_config_path


def test_ini_loads_percent_secret_and_relative_paths(tmp_path: Path) -> None:
    config = tmp_path / "x3guilds-ai.ini"
    config.write_text(
        """[general]
provider = gigachat
[gigachat]
credentials = abc%def
[security]
api_password = local-secret
[paths]
database = state/memory.sqlite3
""",
        encoding="utf-8",
    )
    settings = Settings.load(config)
    assert settings.provider == "gigachat"
    assert settings.gigachat_credentials == "abc%def"
    assert settings.api_password == "local-secret"
    assert settings.database_path == tmp_path / "state/memory.sqlite3"


def test_environment_overrides_ini(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "x3guilds-ai.ini"
    config.write_text("[general]\nprovider = mock\n", encoding="utf-8")
    monkeypatch.setenv("X3AI_PROVIDER", "gigachat")
    monkeypatch.setenv("X3AI_GIGACHAT_CREDENTIALS", "env-secret")
    settings = Settings.load(config)
    assert settings.provider == "gigachat"
    assert settings.gigachat_credentials == "env-secret"


def test_explicit_config_path_is_returned(tmp_path: Path) -> None:
    config = tmp_path / "x3guilds-ai.ini"
    assert detect_config_path(config) == config
