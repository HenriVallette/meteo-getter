"""Codepoints Material Symbols Outlined (même noms que main.html / weather_components.js)."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

# Noms → codepoints (cmap MaterialSymbolsOutlined.ttf)
ICON = {
  "flare": 0xE3E4,
  "air": 0xEFD8,
  "thermostat": 0xF076,
  "humidity_percentage": 0xF87E,
  "place": 0xF1DB,
  "pin_drop": 0xE55E,
  "wb_sunny": 0xE430,
  "wb_twilight": 0xE1C6,
  "wb_twilight_2": 0xFFF1F,
  "mood": 0xEA22,
  "water_drop": 0xE798,
  "rainy": 0xF176,
  "rainy_light": 0xF61E,
  "rainy_heavy": 0xF61F,
  "sunny": 0xE81A,
  "cloud": 0xF15C,
  "partly_cloudy_day": 0xF172,
  "foggy": 0xE818,
  "thunderstorm": 0xEBDB,
  "weather_snowy": 0xE2CD,
  "weather_hail": 0xF67F,
  "snowing_heavy": 0xF61C,
}

WEATHER_CODE_ICON = {
  0: "sunny",
  1: "partly_cloudy_day",
  2: "partly_cloudy_day",
  3: "cloud",
  45: "foggy",
  48: "foggy",
  51: "rainy_light",
  53: "rainy_light",
  55: "rainy",
  56: "weather_hail",
  57: "weather_hail",
  61: "rainy_light",
  63: "rainy",
  65: "rainy_heavy",
  66: "weather_hail",
  67: "weather_hail",
  71: "weather_snowy",
  73: "weather_snowy",
  75: "snowing_heavy",
  77: "weather_snowy",
  80: "rainy_light",
  81: "rainy",
  82: "rainy_heavy",
  85: "weather_snowy",
  86: "snowing_heavy",
  95: "thunderstorm",
  96: "thunderstorm",
  99: "thunderstorm",
}

_FONT_PATHS = (
  Path(__file__).resolve().parent / "MaterialSymbols.ttf",
  Path(__file__).resolve().parent / "MaterialSymbolsGstatic.ttf",
  Path(__file__).resolve().parent / "MaterialSymbolsOutlined.ttf",
)


def icon_char(name: str) -> str:
  code = ICON.get(name)
  if code is None:
    return "?"
  return chr(code)


def weather_icon_name(code: int | None) -> str:
  if code is None:
    return "cloud"
  try:
    return WEATHER_CODE_ICON.get(int(code), "cloud")
  except (TypeError, ValueError):
    return "cloud"


def weather_icon_char(code: int | None) -> str:
  return icon_char(weather_icon_name(code))


def load_icon_font(
  size: int,
  *,
  weight: int = 400,
  optical_size: int = 24,
  fill: int = 0,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  """Charge Material Symbols avec axes proches du CSS Google Fonts."""
  for path in _FONT_PATHS:
    if path.exists():
      try:
        font = ImageFont.truetype(str(path), size=size)
        try:
          # Fill, Grade, Optical Size, Weight
          font.set_variation_by_axes([fill, 0, optical_size, weight])
        except Exception:
          pass
        return font
      except OSError:
        continue
  return ImageFont.load_default()
