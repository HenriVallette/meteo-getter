"""Cache JSON fichier (remplace localStorage)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import CACHE_DIR


def ensure_cache_dir() -> None:
  CACHE_DIR.mkdir(parents=True, exist_ok=True)


def read_json_cache(path: Path) -> Any | None:
  try:
    if not path.exists():
      return None
    return json.loads(path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return None


def write_json_cache(path: Path, value: Any) -> None:
  try:
    ensure_cache_dir()
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
  except OSError:
    pass
