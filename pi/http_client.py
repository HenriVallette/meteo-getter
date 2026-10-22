"""Client HTTP minimal (urllib) avec timeout."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout: float = 10) -> Any:
  request_headers = {"Accept": "application/json"}
  if headers:
    request_headers.update(headers)

  request = urllib.request.Request(url, headers=request_headers)

  try:
    with urllib.request.urlopen(request, timeout=timeout) as response:
      if response.status < 200 or response.status >= 300:
        raise RuntimeError(f"Le service distant a répondu avec le statut {response.status}.")
      return json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as error:
    raise RuntimeError(
      f"Le service distant a répondu avec le statut {error.code}."
    ) from error
  except urllib.error.URLError as error:
    raise RuntimeError("Le service distant n'a pas répondu à temps.") from error
