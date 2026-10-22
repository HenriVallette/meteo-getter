#!/usr/bin/env python3
"""Boucle kiosk Meteo Getter pour Raspberry Pi Zero 2W."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from config import JOKE_REFRESH_S, LOCATION, PLACES, WEATHER_REFRESH_S
from display import init_display, shutdown, show_image, wait_with_events
from jokes import (
  fetch_joke,
  is_joke_cache_fresh,
  load_joke_cache,
  load_dotenv,
  save_joke_cache,
)
from render import render_dashboard
from weather import (
  fetch_places_forecasts,
  fetch_weather,
  is_weather_for_location,
  load_places_cache,
  load_weather_cache,
  save_places_cache,
  save_weather_cache,
)

_running = True


def _handle_signal(signum, frame) -> None:  # noqa: ARG001
  global _running
  _running = False


def refresh_weather_state(latest_weather, latest_places):
  status = ""
  weather = latest_weather
  places = latest_places

  try:
    weather = fetch_weather(LOCATION)
    save_weather_cache(weather)
  except Exception as error:  # noqa: BLE001
    status = f"Météo: {error}"
    cached = load_weather_cache()
    if is_weather_for_location(cached, LOCATION):
      weather = cached

  try:
    places = fetch_places_forecasts(PLACES)
    save_places_cache(places)
  except Exception as error:  # noqa: BLE001
    status = (status + " | " if status else "") + f"Lieux: {error}"
    cached_places = load_places_cache()
    if cached_places:
      places = cached_places

  return weather, places, status


def refresh_joke_state(latest_joke, force: bool = False):
  status = ""
  joke = latest_joke

  if not force and is_joke_cache_fresh(joke):
    return joke, status

  try:
    joke = fetch_joke()
    save_joke_cache(joke)
  except Exception as error:  # noqa: BLE001
    status = f"Blague: {error}"
    cached = load_joke_cache()
    if cached:
      joke = cached

  return joke, status


def run(fullscreen: bool = True) -> int:
  global _running

  signal.signal(signal.SIGINT, _handle_signal)
  signal.signal(signal.SIGTERM, _handle_signal)
  load_dotenv()

  latest_weather = load_weather_cache()
  if not is_weather_for_location(latest_weather, LOCATION):
    latest_weather = None
  latest_places = load_places_cache() or []
  latest_joke = load_joke_cache()

  init_display(fullscreen=fullscreen)

  image = render_dashboard(latest_weather, latest_places, latest_joke, "Chargement…")
  if not show_image(image):
    shutdown()
    return 0

  next_joke_refresh = 0.0

  while _running:
    weather, places, weather_status = refresh_weather_state(latest_weather, latest_places)
    latest_weather = weather
    latest_places = places

    now = time.time()
    joke_status = ""
    if now >= next_joke_refresh or not is_joke_cache_fresh(latest_joke):
      latest_joke, joke_status = refresh_joke_state(latest_joke, force=True)
      next_joke_refresh = now + JOKE_REFRESH_S

    status = " | ".join(part for part in (weather_status, joke_status) if part)
    image = render_dashboard(latest_weather, latest_places, latest_joke, status)
    if not show_image(image):
      break

    if not wait_with_events(WEATHER_REFRESH_S * 1000):
      break

  shutdown()
  return 0


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Meteo Getter kiosk Pi Zero 2W")
  parser.add_argument(
    "--windowed",
    action="store_true",
    help="Lancer en fenêtre (développement)",
  )
  args = parser.parse_args(argv)
  return run(fullscreen=not args.windowed)


if __name__ == "__main__":
  sys.exit(main())
