"""Récupération et normalisation Open-Meteo (port de logic.js)."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from config import (
  FIVE_MINUTE_SECONDS,
  FIFTEEN_MINUTE_SECONDS,
  NEXT_DAY_HOUR,
  PLACES_CACHE_FILE,
  RAIN_HOUR_STEPS,
  REQUEST_TIMEOUT_S,
  WEATHER_API_URL,
  WEATHER_CACHE_FILE,
)
from cache import read_json_cache, write_json_cache
from http_client import fetch_json


def build_query_string(parameters: dict[str, Any]) -> str:
  prepared: dict[str, str] = {}
  for key, value in parameters.items():
    if isinstance(value, (list, tuple)):
      prepared[key] = ",".join(str(item) for item in value)
    else:
      prepared[key] = str(value)
  return urlencode(prepared)


def fetch_weather(location: dict[str, Any]) -> dict[str, Any]:
  parameters = {
    "latitude": location["latitude"],
    "longitude": location["longitude"],
    "models": "best_match",
    "timezone": "auto",
    "timeformat": "unixtime",
    "forecast_days": 8,
    "forecast_minutely_15": 8,
    "current": [
      "temperature_2m",
      "apparent_temperature",
      "relative_humidity_2m",
      "precipitation",
      "rain",
      "weather_code",
      "wind_speed_10m",
      "is_day",
    ],
    "minutely_15": ["precipitation", "rain"],
    "hourly": [
      "temperature_2m",
      "apparent_temperature",
      "relative_humidity_2m",
      "precipitation_probability",
      "precipitation",
      "rain",
      "weather_code",
      "wind_speed_10m",
    ],
    "daily": [
      "weather_code",
      "temperature_2m_min",
      "temperature_2m_max",
      "apparent_temperature_min",
      "apparent_temperature_max",
      "uv_index_max",
      "precipitation_sum",
      "precipitation_probability_max",
      "sunrise",
      "sunset",
    ],
  }
  url = f"{WEATHER_API_URL}?{build_query_string(parameters)}"
  response = fetch_json(url, timeout=REQUEST_TIMEOUT_S)
  return normalize_weather_response(response, location)


def normalize_weather_response(response: dict[str, Any], location: dict[str, Any]) -> dict[str, Any]:
  if not response.get("current") or not response.get("hourly") or not response.get("daily"):
    raise RuntimeError("La réponse météo est incomplète.")

  current_timestamp = response["current"]["time"]
  hourly_items = [
    item
    for item in map_series(response["hourly"])
    if item["time"] >= current_timestamp
  ][:12]
  minutely_items = (
    to_five_minute_rain(response["minutely_15"], current_timestamp)
    if response.get("minutely_15")
    else []
  )

  return {
    "location": location,
    "timezone": response.get("timezone") or location.get("timezone") or "UTC",
    "utc_offset_seconds": response.get("utc_offset_seconds") or 0,
    "updated_at": int(time.time() * 1000),
    "current": dict(response["current"]),
    "hourly": hourly_items,
    "minutely": minutely_items,
    "daily": map_series(response["daily"])[:8],
  }


def select_daily_forecast(
  daily: list[dict[str, Any]],
  timezone: str,
  now: datetime | None = None,
) -> dict[str, Any] | None:
  current = now or datetime.now(tz=ZoneInfo(timezone))
  index = 1 if get_hour(current, timezone) >= NEXT_DAY_HOUR else 0
  if index < len(daily):
    return daily[index]
  return None


def map_series(series: dict[str, Any]) -> list[dict[str, Any]]:
  times = series.get("time") or []
  items: list[dict[str, Any]] = []

  for index, timestamp in enumerate(times):
    item: dict[str, Any] = {"time": timestamp}
    for key, values in series.items():
      if key != "time" and isinstance(values, list):
        item[key] = values[index] if index < len(values) else None
    items.append(item)

  return items


def to_five_minute_rain(series: dict[str, Any], current_timestamp: int) -> list[dict[str, Any]]:
  intervals = [
    item
    for item in map_series(series)
    if item["time"] > current_timestamp
  ][: RAIN_HOUR_STEPS // 3]

  result: list[dict[str, Any]] = []
  for item in intervals:
    window_start = item["time"] - FIFTEEN_MINUTE_SECONDS
    for step in (0, 1, 2):
      result.append({
        "time": window_start + step * FIVE_MINUTE_SECONDS,
        "precipitation": split_fifteen_minute_amount(item.get("precipitation")),
        "rain": split_fifteen_minute_amount(item.get("rain")),
      })
  return result


def split_fifteen_minute_amount(value: Any) -> float | None:
  if value is None:
    return None
  return float(value) / 3


def get_hour(date: datetime, timezone: str) -> int:
  localized = date.astimezone(ZoneInfo(timezone))
  return localized.hour


def save_weather_cache(weather: dict[str, Any]) -> None:
  write_json_cache(WEATHER_CACHE_FILE, weather)


def load_weather_cache() -> dict[str, Any] | None:
  data = read_json_cache(WEATHER_CACHE_FILE)
  return data if isinstance(data, dict) else None


def save_places_cache(places: list[dict[str, Any]]) -> None:
  write_json_cache(PLACES_CACHE_FILE, places)


def load_places_cache() -> list[dict[str, Any]] | None:
  data = read_json_cache(PLACES_CACHE_FILE)
  return data if isinstance(data, list) else None


def is_weather_for_location(weather: dict[str, Any] | None, location: dict[str, Any]) -> bool:
  if not weather or not isinstance(weather.get("location"), dict):
    return False
  cached = weather["location"]
  try:
    return (
      abs(float(cached["latitude"]) - float(location["latitude"])) < 0.01
      and abs(float(cached["longitude"]) - float(location["longitude"])) < 0.01
    )
  except (KeyError, TypeError, ValueError):
    return False


def fetch_places_forecasts(places: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> list[dict[str, Any]]:
  results: list[dict[str, Any]] = []

  for place in places:
    try:
      weather = fetch_weather(place)
      forecast = select_daily_forecast(weather["daily"], weather["timezone"])
      results.append({
        "id": place["id"],
        "name": place["name"],
        "period": (
          "—"
          if forecast is None
          else ("Aujourd'hui" if forecast is weather["daily"][0] else "Demain")
        ),
        "minimum": None if forecast is None else forecast.get("temperature_2m_min"),
        "maximum": None if forecast is None else forecast.get("temperature_2m_max"),
        "rain_probability": (
          None if forecast is None else forecast.get("precipitation_probability_max")
        ),
        "error": "" if forecast is not None else "Prévision du lendemain indisponible.",
      })
    except Exception as error:  # noqa: BLE001 — isolation par lieu
      results.append({
        "id": place["id"],
        "name": place["name"],
        "period": "—",
        "minimum": None,
        "maximum": None,
        "rain_probability": None,
        "error": str(error),
      })

  return results
