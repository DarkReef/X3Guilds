from __future__ import annotations

import os
from pathlib import Path


LOG_FILE_NAME = "log09980.txt"


def candidate_x3fl_directories() -> list[Path]:
    candidates: list[Path] = []
    home = Path.home()
    user_profile = Path(os.environ.get("USERPROFILE", home))
    one_drive = os.environ.get("OneDrive")

    for root in [user_profile / "Documents", user_profile / "My Documents", home / "Documents"]:
        candidates.extend([root / "Egosoft" / "X3FL", root / "EgoSoft" / "X3FL"])
    if one_drive:
        root = Path(one_drive) / "Documents"
        candidates.extend([root / "Egosoft" / "X3FL", root / "EgoSoft" / "X3FL"])

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique


def detect_request_log() -> Path:
    existing_dirs = [path for path in candidate_x3fl_directories() if path.exists()]
    for directory in existing_dirs:
        exact = directory / LOG_FILE_NAME
        if exact.exists():
            return exact
    if existing_dirs:
        return existing_dirs[0] / LOG_FILE_NAME
    return candidate_x3fl_directories()[0] / LOG_FILE_NAME
