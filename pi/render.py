"""Composition du dashboard 1920x1080 avec Pillow."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from config import SCREEN, SCREEN_HEIGHT, SCREEN_WIDTH
from weather_labels import get_weather_label

BG = (18, 24, 32)
PANEL = (28, 36, 48)
PANEL_ALT = (34, 44, 58)
TEXT = (236, 240, 245)
MUTED = (160, 172, 188)
ACCENT = (120, 190, 255)
RAIN = (96, 165, 250)
WARN = (255, 180, 80)
ERROR = (220, 90, 90)

FONT_CANDIDATES = (
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
  "C:/Windows/Fonts/arial.ttf",
  "C:/Windows/Fonts/segoeui.ttf",
)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  names = FONT_CANDIDATES
  if bold:
    names = (
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
      *FONT_CANDIDATES,
    )
  for path in names:
    if Path(path).exists():
      try:
        return ImageFont.truetype(path, size=size)
      except OSError:
        continue
  return ImageFont.load_default()


def format_temperature(value: Any) -> str:
  if value is None:
    return "—"
  return f"{float(value):.1f}°C".replace(".", ",")


def format_number(value: Any, digits: int = 1) -> str:
  if value is None:
    return "—"
  formatted = f"{float(value):.{digits}f}"
  return formatted.replace(".", ",")


def format_time(timestamp: Any, timezone: str) -> str:
  try:
    seconds = float(timestamp)
    dt = datetime.fromtimestamp(seconds, tz=ZoneInfo(timezone))
    return dt.strftime("%H:%M")
  except (TypeError, ValueError, OSError):
    return "—"


def format_clock_time(timestamp: Any, timezone: str) -> str:
  if timestamp is None:
    return "—"
  if isinstance(timestamp, str):
    try:
      parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
      return parsed.astimezone(ZoneInfo(timezone)).strftime("%H:%M")
    except ValueError:
      return "—"
  return format_time(timestamp, timezone)


def format_day(timestamp: Any, timezone: str) -> str:
  try:
    dt = datetime.fromtimestamp(float(timestamp), tz=ZoneInfo(timezone))
    label = dt.strftime("%a")
    return label[:1].upper() + label[1:]
  except (TypeError, ValueError, OSError):
    return "—"


def format_update_time(timestamp_ms: Any) -> str:
  try:
    dt = datetime.fromtimestamp(float(timestamp_ms) / 1000)
    return dt.strftime("%d/%m/%Y %H:%M")
  except (TypeError, ValueError, OSError):
    return "—"


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, int, int]) -> None:
  draw.rounded_rectangle(box, radius=16, fill=fill)


def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill=TEXT) -> None:
  draw.text(xy, text, font=font, fill=fill)


def render_dashboard(
  weather: dict[str, Any] | None,
  places: list[dict[str, Any]] | None,
  joke: dict[str, Any] | None,
  status_message: str = "",
) -> Image.Image:
  image = Image.new("RGB", SCREEN, BG)
  draw = ImageDraw.Draw(image)

  font_title = _load_font(42, bold=True)
  font_large = _load_font(72, bold=True)
  font_md = _load_font(28)
  font_sm = _load_font(22)
  font_xs = _load_font(18)

  # Header
  _text(draw, (48, 28), "Meteo Getter", font_title, ACCENT)
  updated = format_update_time(weather.get("updated_at")) if weather else "—"
  _text(draw, (48, 82), f"Mise à jour : {updated}", font_sm, MUTED)
  if status_message:
    _text(draw, (700, 82), status_message, font_sm, WARN)

  # Current panel
  _rounded_rect(draw, (40, 120, 760, 620), PANEL)
  if weather:
    location = weather.get("location") or {}
    current = weather.get("current") or {}
    today = (weather.get("daily") or [{}])[0]
    timezone = weather.get("timezone") or "UTC"
    details = ", ".join(
      part for part in (location.get("admin1"), location.get("country")) if part
    )

    _text(draw, (64, 140), location.get("name") or "Localisation", font_title)
    _text(draw, (64, 195), details, font_sm, MUTED)
    _text(
      draw,
      (64, 235),
      get_weather_label(current.get("weather_code")),
      font_md,
      ACCENT,
    )
    _text(draw, (64, 290), format_temperature(current.get("temperature_2m")), font_large)
    _text(
      draw,
      (64, 380),
      f"{format_temperature(current.get('apparent_temperature'))} ressenti",
      font_md,
      MUTED,
    )

    metrics = [
      ("Vent", f"{format_number(current.get('wind_speed_10m'))} km/h"),
      ("Min / Max", f"{format_temperature(today.get('temperature_2m_min'))} / {format_temperature(today.get('temperature_2m_max'))}"),
      ("UV", format_number(today.get("uv_index_max"), 0)),
      ("Pluie jour", f"{int(round(today.get('precipitation_probability_max') or 0))} %"),
      ("Lever", format_clock_time(today.get("sunrise"), timezone)),
      ("Coucher", format_clock_time(today.get("sunset"), timezone)),
    ]
    y = 440
    for label, value in metrics:
      _text(draw, (64, y), f"{label} : {value}", font_sm)
      y += 28
  else:
    _text(draw, (64, 160), "En attente des données météo…", font_md, MUTED)

  # Rain strip
  _rounded_rect(draw, (40, 640, 760, 1040), PANEL_ALT)
  _text(draw, (64, 660), "Prévision 5 min", font_md, ACCENT)
  if weather and weather.get("minutely"):
    x = 64
    y = 710
    for index, item in enumerate(weather["minutely"][:12]):
      precip = item.get("precipitation")
      if precip is None:
        precip = item.get("rain") or 0
      col = x + (index % 6) * 110
      row = y + (index // 6) * 140
      _rounded_rect(draw, (col, row, col + 100, row + 120), PANEL)
      _text(draw, (col + 12, row + 16), format_time(item.get("time"), weather["timezone"]), font_xs, MUTED)
      _text(draw, (col + 12, row + 50), f"{format_number(precip, 1)} mm", font_sm, RAIN if precip else MUTED)
  else:
    _text(draw, (64, 720), "Prévision à 5 minutes indisponible.", font_sm, MUTED)

  # Hourly
  _rounded_rect(draw, (790, 120, 1880, 380), PANEL)
  _text(draw, (814, 140), "Prochaines heures", font_md, ACCENT)
  if weather:
    x = 814
    for item in weather.get("hourly") or []:
      _rounded_rect(draw, (x, 190, x + 85, 350), PANEL_ALT)
      _text(draw, (x + 10, 205), format_time(item.get("time"), weather["timezone"]), font_xs, MUTED)
      _text(draw, (x + 10, 245), format_temperature(item.get("temperature_2m")), font_sm)
      _text(
        draw,
        (x + 10, 290),
        f"{int(round(item.get('precipitation_probability') or 0))}%",
        font_xs,
        RAIN,
      )
      x += 90

  # Daily
  _rounded_rect(draw, (790, 400, 1880, 620), PANEL)
  _text(draw, (814, 420), "Semaine", font_md, ACCENT)
  if weather:
    x = 814
    for item in (weather.get("daily") or [])[1:8]:
      _rounded_rect(draw, (x, 470, x + 145, 590), PANEL_ALT)
      _text(draw, (x + 12, 485), format_day(item.get("time"), weather["timezone"]), font_sm)
      _text(
        draw,
        (x + 12, 525),
        f"{format_temperature(item.get('temperature_2m_min'))}",
        font_xs,
        MUTED,
      )
      _text(
        draw,
        (x + 12, 550),
        f"{format_temperature(item.get('temperature_2m_max'))}",
        font_xs,
      )
      x += 152

  # Places
  _rounded_rect(draw, (790, 640, 1330, 880), PANEL)
  _text(draw, (814, 660), "Lieux", font_md, ACCENT)
  y = 710
  for place in places or []:
    name = place.get("name") or place.get("id") or "—"
    period = place.get("period") or "—"
    line = (
      f"{name} ({period})  "
      f"{format_temperature(place.get('minimum'))} / {format_temperature(place.get('maximum'))}  "
      f"pluie {('—' if place.get('rain_probability') is None else str(int(round(place['rain_probability']))) + '%')}"
    )
    _text(draw, (814, y), line, font_sm)
    if place.get("error"):
      _text(draw, (814, y + 26), str(place["error"])[:60], font_xs, ERROR)
      y += 70
    else:
      y += 50

  # Joke
  _rounded_rect(draw, (1350, 640, 1880, 1040), PANEL)
  _text(draw, (1374, 660), "Blague", font_md, ACCENT)
  if joke:
    _wrap_text(draw, joke.get("joke") or "", (1374, 710), 470, font_sm, TEXT)
    answer = joke.get("answer") or ""
    if answer:
      _wrap_text(draw, answer, (1374, 860), 470, font_sm, MUTED)
  else:
    _text(draw, (1374, 720), "Aucune blague chargée.", font_sm, MUTED)

  # Footer bar
  draw.rectangle((0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(12, 16, 22))
  _text(draw, (48, SCREEN_HEIGHT - 24), "Pi Zero 2W kiosk", font_xs, MUTED)

  return image


def _wrap_text(
  draw: ImageDraw.ImageDraw,
  text: str,
  origin: tuple[int, int],
  max_width: int,
  font,
  fill,
) -> None:
  words = text.split()
  lines: list[str] = []
  current = ""
  for word in words:
    candidate = f"{current} {word}".strip()
    bbox = draw.textbbox((0, 0), candidate, font=font)
    if bbox[2] - bbox[0] <= max_width:
      current = candidate
    else:
      if current:
        lines.append(current)
      current = word
  if current:
    lines.append(current)

  x, y = origin
  for line in lines[:6]:
    _text(draw, (x, y), line, font, fill)
    y += 28
