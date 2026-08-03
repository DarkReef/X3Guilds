from pathlib import Path

from x3guilds_ai.paths import candidate_x3fl_directories


def test_candidate_paths_include_x3fl(monkeypatch) -> None:
    monkeypatch.setenv("USERPROFILE", str(Path("C:/Users/Test")))
    paths = candidate_x3fl_directories()
    assert any(path.name == "X3FL" for path in paths)
