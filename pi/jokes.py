"""Blagues API + cache."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urlencode

from config import (
  BLAGUES_API_URL,
  ENV_FILE,
  JOKE_CACHE_FILE,
  JOKE_REFRESH_S,
  REQUEST_TIMEOUT_S,
)
from cache import read_json_cache, write_json_cache
from http_client import fetch_json


def load_dotenv(path=ENV_FILE) -> None:
  if not path.exists():
    return

  for line in path.read_text(encoding="utf-8").splitlines():
    trimmed = line.strip()
    if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
      continue
    key, value = trimmed.split("=", 1)
    key = key.strip()
    value = value.strip().strip("\"'")
    if key and key not in os.environ:
      os.environ[key] = value


def get_blagues_api_token() -> str:
  load_dotenv()
  return os.environ.get("BLAGUES_API_TOKEN", "").strip()


def is_joke_cache_fresh(joke: dict[str, Any] | None, now_ms: int | None = None) -> bool:
  if not joke or not joke.get("fetched_at"):
    return False
  current = now_ms if now_ms is not None else int(time.time() * 1000)
  return current - int(joke["fetched_at"]) < JOKE_REFRESH_S * 1000


def save_joke_cache(joke: dict[str, Any]) -> None:
  write_json_cache(JOKE_CACHE_FILE, joke)


def load_joke_cache() -> dict[str, Any] | None:
  data = read_json_cache(JOKE_CACHE_FILE)
  return data if isinstance(data, dict) else None


def fetch_joke() -> dict[str, Any]:
  token = get_blagues_api_token()
  if not token:
    raise RuntimeError(
      "Token Blagues API manquant. Ajoutez BLAGUES_API_TOKEN dans pi/.env."
    )

  query = urlencode({"disallow": ["dark", "limit"]}, doseq=True)
  url = f"{BLAGUES_API_URL}?{query}"
  response = fetch_json(
    url,
    headers={"Authorization": f"Bearer {token}"},
    timeout=REQUEST_TIMEOUT_S,
  )

  if not response or not response.get("joke"):
    raise RuntimeError("La réponse blague est incomplète.")

  return {
    "id": response.get("id"),
    "type": response.get("type"),
    "joke": response["joke"],
    "answer": response.get("answer") or "",
    "fetched_at": int(time.time() * 1000),
  }
