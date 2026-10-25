"""
Composition du dashboard 1920×1080 — positions figées d'après le design.

Grille mesurée (ancre = panneau orange) :
  padding X = 48, gap = 18
  row1 = 417, row2 = row3 = 278  (ratio 1,5 / 1 / 1)
  cols ≈ 889 / 490 / 409

  [ current ] [ metrics orange ] [ places ]
  [ ----------- hourly pleine largeur ----------- ]
  [ ----- daily (col1+2) ----- ] [ plus-panel ]
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from config import SCREEN, SCREEN_HEIGHT, SCREEN_WIDTH
from icons import icon_char, load_icon_font, weather_icon_char, weather_icon_name
from weather import select_daily_forecast
from weather_labels import get_weather_label

# Palette (design / CSS)
BG_TOP = (18, 20, 13)
BG_BOTTOM = (58, 42, 22)
TEXT = (255, 246, 234)
MUTED = (215, 199, 164)
PRIMARY_SOFT = (255, 177, 90)
BORDER = (255, 166, 61, 72)
CARD_TOP = (49, 56, 31)
CARD_BOTTOM = (29, 33, 20)
CARD_INNER = (23, 25, 16)
RAIN_CELL = (61, 74, 34)
METRICS_TOP = (240, 122, 34)
METRICS_BOTTOM = (196, 81, 0)
METRICS_TEXT = (42, 22, 8)
PLACE_A = (85, 99, 50)
PLACE_B = (138, 75, 22)
ERROR = (170, 44, 44)
WARN = (255, 210, 124)

# Layout figé 1920×1080 — mesuré sur le design (panneau orange = ancre)
PAGE_PAD_X = 48
GAP = 18
CARD_PAD = 24
INNER_GAP = 12
RADIUS = 16
RADIUS_INNER = 12

# Boîtes des panneaux (x0, y0, x1, y1) — row1=417, row2=row3=278, gap=18
CURRENT_BOX = (48, 45, 937, 462)
METRICS_BOX = (955, 45, 1445, 462)
PLACES_BOX = (1463, 45, 1872, 462)
HOURLY_BOX = (48, 480, 1872, 758)
DAILY_BOX = (48, 776, 1445, 1054)
PLUS_BOX = (1463, 776, 1872, 1054)

DAY_FR = ("Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam.", "Dim.")

FONT_REGULAR = (
  "C:/Windows/Fonts/segoeui.ttf",
  "C:/Windows/Fonts/arial.ttf",
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
FONT_BOLD = (
  "C:/Windows/Fonts/segoeuib.ttf",
  "C:/Windows/Fonts/arialbd.ttf",
  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  for path in (FONT_BOLD if bold else FONT_REGULAR):
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
  return f"{float(value):.{digits}f}".replace(".", ",")


def format_precip_mm(value: Any) -> str:
  if value is None:
    return "— mm"
  amount = float(value)
  if abs(amount) < 0.05:
    return "0 mm"
  return f"{amount:.1f} mm".replace(".", ",")


def format_time(timestamp: Any, timezone: str) -> str:
  try:
    dt = datetime.fromtimestamp(float(timestamp), tz=ZoneInfo(timezone))
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
    return DAY_FR[dt.weekday()]
  except (TypeError, ValueError, OSError):
    return "—"


def format_update_time(timestamp_ms: Any) -> str:
  try:
    dt = datetime.fromtimestamp(float(timestamp_ms) / 1000)
    return dt.strftime("%d/%m/%Y %H:%M")
  except (TypeError, ValueError, OSError):
    return "—"


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
  return (
    int(a[0] + (b[0] - a[0]) * t),
    int(a[1] + (b[1] - a[1]) * t),
    int(a[2] + (b[2] - a[2]) * t),
  )


def _fill_vertical_gradient_fast(image, box, top, bottom) -> None:
  x0, y0, x1, y1 = box
  width = max(x1 - x0, 1)
  height = max(y1 - y0, 1)
  band = Image.new("RGB", (1, height))
  for y in range(height):
    band.putpixel((0, y), _lerp(top, bottom, y / max(height - 1, 1)))
  image.paste(band.resize((width, height), Image.Resampling.BILINEAR), (x0, y0))


def _rounded_card(image, box, top, bottom, radius: int = RADIUS) -> None:
  x0, y0, x1, y1 = box
  grad = Image.new("RGB", (x1 - x0, y1 - y0))
  _fill_vertical_gradient_fast(grad, (0, 0, x1 - x0, y1 - y0), top, bottom)
  mask = Image.new("L", (x1 - x0, y1 - y0), 0)
  ImageDraw.Draw(mask).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=radius, fill=255)
  image.paste(grad, (x0, y0), mask)
  ImageDraw.Draw(image, "RGBA").rounded_rectangle(box, radius=radius, outline=BORDER, width=1)


def _inner_tile(image, box, fill_rgba, radius: int = RADIUS_INNER) -> None:
  x0, y0, x1, y1 = box
  w, h = x1 - x0, y1 - y0
  if w <= 0 or h <= 0:
    return
  cell = Image.new("RGBA", (w, h), (0, 0, 0, 0))
  ImageDraw.Draw(cell).rounded_rectangle(
    (0, 0, w - 1, h - 1),
    radius=radius,
    fill=fill_rgba,
    outline=(255, 177, 90, 50),
  )
  image.paste(cell, (x0, y0), cell)


def _text(draw, xy, text, font, fill=TEXT) -> None:
  draw.text(xy, text, font=font, fill=fill)


def _icon(draw, xy, name, font, fill=PRIMARY_SOFT) -> None:
  draw.text(xy, icon_char(name), font=font, fill=fill)


def _centered_icon(draw, box, name, font, fill=PRIMARY_SOFT) -> None:
  x0, y0, x1, y1 = box
  ch = icon_char(name)
  bbox = draw.textbbox((0, 0), ch, font=font)
  w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
  draw.text(
    (x0 + (x1 - x0 - w) // 2 - bbox[0], y0 + (y1 - y0 - h) // 2 - bbox[1]),
    ch,
    font=font,
    fill=fill,
  )


def _centered_text(draw, box, text, font, fill=TEXT) -> None:
  x0, y0, x1, y1 = box
  bbox = draw.textbbox((0, 0), text, font=font)
  w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
  draw.text(
    (x0 + (x1 - x0 - w) // 2 - bbox[0], y0 + (y1 - y0 - h) // 2 - bbox[1]),
    text,
    font=font,
    fill=fill,
  )


def _wrap_text(draw, text, origin, max_width, font, fill, max_lines=6, line_gap=26, align="left") -> int:
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
  for line in lines[:max_lines]:
    if align == "right":
      bbox = draw.textbbox((0, 0), line, font=font)
      _text(draw, (x + max_width - (bbox[2] - bbox[0]), y), line, font, fill)
    else:
      _text(draw, (x, y), line, font, fill)
    y += line_gap
  return y


def _box_size(box: tuple[int, int, int, int]) -> tuple[int, int]:
  x0, y0, x1, y1 = box
  return x1 - x0, y1 - y0


def render_dashboard(
  weather: dict[str, Any] | None,
  places: list[dict[str, Any]] | None,
  joke: dict[str, Any] | None,
  status_message: str = "",
) -> Image.Image:
  assert SCREEN == (1920, 1080)

  image = Image.new("RGB", SCREEN, BG_TOP)
  _fill_vertical_gradient_fast(image, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), BG_TOP, BG_BOTTOM)

  glow = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
  glow_draw = ImageDraw.Draw(glow)
  glow_draw.ellipse((-200, -280, 520, 420), fill=(255, 122, 26, 40))
  glow_draw.ellipse((1380, -120, 2100, 520), fill=(122, 145, 46, 45))
  image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
  draw = ImageDraw.Draw(image)

  font_xs = _load_font(14)
  font_sm = _load_font(16)
  font_md = _load_font(18)
  font_md_b = _load_font(18, bold=True)
  font_h2 = _load_font(24, bold=True)
  font_h1 = _load_font(28, bold=True)
  font_temp = _load_font(96, bold=True)
  font_metric = _load_font(28, bold=True)
  font_big_metric = _load_font(32, bold=True)
  font_card = _load_font(20, bold=True)
  font_joke = _load_font(22, bold=True)
  font_icon_xl = load_icon_font(110)
  font_icon_lg_plus = load_icon_font(60)
  font_icon_lg = load_icon_font(40)
  font_icon_md = load_icon_font(32)
  font_icon_sm = load_icon_font(28)
  font_icon_xs = load_icon_font(22)
  font_icon_metric = load_icon_font(36)

  # --- Status ---
  updated = format_update_time(weather.get("updated_at")) if weather else "—"
  update_label = f"Mise à jour : {updated}"
  ub = draw.textbbox((0, 0), update_label, font=font_xs)
  _text(
    draw,
    (SCREEN_WIDTH - PAGE_PAD_X - (ub[2] - ub[0]), 12),
    update_label,
    font_xs,
    MUTED,
  )
  if status_message:
    _text(draw, (PAGE_PAD_X, 12), status_message[:70], font_xs, WARN)

  timezone = (weather or {}).get("timezone") or "UTC"
  location = (weather or {}).get("location") or {}
  current = (weather or {}).get("current") or {}
  daily = (weather or {}).get("daily") or []
  # À partir de 21h : min/max, UV, pluie, lever/coucher = prévisions du lendemain
  focus_day = select_daily_forecast(daily, timezone) or (daily[0] if daily else {})
  focus_label = (
    "Demain"
    if daily and focus_day is not daily[0]
    else "Aujourd'hui"
  )

  # =========================================================================
  # CURRENT PANEL
  # =========================================================================
  x0, y0, x1, y1 = CURRENT_BOX
  panel_w, panel_h = _box_size(CURRENT_BOX)
  _rounded_card(image, CURRENT_BOX, CARD_TOP, CARD_BOTTOM)
  blob = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
  ImageDraw.Draw(blob).ellipse(
    (x1 - 280, y0 - 120, x1 + 80, y0 + 260),
    fill=(255, 138, 42, 40),
  )
  image = Image.alpha_composite(image.convert("RGBA"), blob).convert("RGB")
  draw = ImageDraw.Draw(image)

  ix = x0 + CARD_PAD
  iy = y0 + CARD_PAD

  name = location.get("name") or "Localisation"
  details = ", ".join(p for p in (location.get("admin1"), location.get("country")) if p)
  _icon(draw, (ix, iy + 10), "place", font_icon_md, PRIMARY_SOFT)
  _text(draw, (ix + 42, iy), name, font_h1)
  _text(draw, (ix + 42, iy + 34), details, font_sm, MUTED)

  label = get_weather_label(current.get("weather_code")) if weather else "—"
  lb = draw.textbbox((0, 0), label, font=font_md)
  _text(draw, (x1 - CARD_PAD - (lb[2] - lb[0]), iy + 6), label, font_md, MUTED)

  # Température + icône — zone centrale haute
  temp_y = iy + 62
  temp_label = format_temperature(current.get("temperature_2m"))
  glow_layer = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
  # glow_draw = ImageDraw.Draw(glow_layer)
  # for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
  #   glow_draw.text((ix + 60 + dx, temp_y + dy), temp_label, font=font_temp, fill=(255, 138, 42, 50))
  image = Image.alpha_composite(image.convert("RGBA"), glow_layer).convert("RGB")
  draw = ImageDraw.Draw(image)
  _text(draw, (ix + 60, temp_y), temp_label, font_temp, PRIMARY_SOFT)
  _text(
    draw,
    (ix + 60, temp_y + 124),
    f"{format_temperature(current.get('apparent_temperature'))} ressenti",
    font_md,
    MUTED,
  )
  draw.text(
    (x1 - CARD_PAD - 130, temp_y + 10),
    weather_icon_char(current.get("weather_code")),
    font=font_icon_xl,
    fill=PRIMARY_SOFT,
  )

  # Pluie dans l'heure — bas de carte (~40 % bas)
  rain_title_y = y0 + 268
  _text(draw, (ix, rain_title_y), "Pluie dans l'heure", font_md_b)
  rain_top = rain_title_y + 40
  rain_bottom = y1 - CARD_PAD
  rain_h = rain_bottom - rain_top
  minutely = (weather or {}).get("minutely") or []
  if minutely:
    n = min(12, len(minutely))
    cell_gap = 6
    cell_w = (panel_w - 2 * CARD_PAD - (n - 1) * cell_gap) // n
    for index, item in enumerate(minutely[:n]):
      cx = ix + index * (cell_w + cell_gap)
      _inner_tile(image, (cx, rain_top, cx + cell_w, rain_top + rain_h), (*RAIN_CELL, 210))
      draw = ImageDraw.Draw(image)
      precip = item.get("precipitation")
      if precip is None:
        precip = item.get("rain") or 0
      _centered_text(draw, (cx, rain_top + 6, cx + cell_w, rain_top + 26), format_time(item.get("time"), timezone), font_xs, MUTED)
      rain_icon = "rainy" if precip else "water_drop"
      _centered_icon(draw, (cx, rain_top + 28, cx + cell_w, rain_top + 58), rain_icon, font_icon_xs, PRIMARY_SOFT)
      _centered_text(
        draw,
        (cx, rain_top + rain_h - 28, cx + cell_w, rain_top + rain_h - 6),
        format_precip_mm(precip),
        font_xs,
        TEXT,
      )
  else:
    _text(draw, (ix, rain_top + 8), "Prévision à 5 minutes indisponible pour ce lieu.", font_sm, MUTED)

  # =========================================================================
  # METRICS PANEL (orange)
  # =========================================================================
  x0, y0, x1, y1 = METRICS_BOX
  panel_w, panel_h = _box_size(METRICS_BOX)
  _rounded_card(image, METRICS_BOX, METRICS_TOP, METRICS_BOTTOM)
  draw = ImageDraw.Draw(image)
  _text(draw, (x0 + CARD_PAD, y0 + CARD_PAD), focus_label, font_h2, METRICS_TEXT)

  metrics = [
    ("air", "Vent", f"{format_number(current.get('wind_speed_10m'))} km/h"),
    (
      "thermostat",
      "Min. / Max.",
      f"{format_temperature(focus_day.get('temperature_2m_min')).replace("C", "")} / {format_temperature(focus_day.get('temperature_2m_max')).replace("C", "")}",
    ),
    ("flare", "Indice UV", format_number(focus_day.get("uv_index_max"), 1)),
    ("humidity_percentage", "Pluie", f"{int(round(focus_day.get('precipitation_probability_max') or 0))}%"),
  ]
  grid_x = x0 + CARD_PAD
  grid_y = y0 + CARD_PAD + 42
  grid_w = panel_w - 2 * CARD_PAD
  grid_h = panel_h - (CARD_PAD + 42) - CARD_PAD
  mw = (grid_w - INNER_GAP) // 2
  mh = (grid_h - INNER_GAP) // 2
  for index, (icon_name, title, value) in enumerate(metrics):
    mx = grid_x + (index % 2) * (mw + INNER_GAP)
    my = grid_y + (index // 2) * (mh + INNER_GAP)
    _inner_tile(image, (mx, my, mx + mw, my + mh), (255, 246, 234, 55))
    draw = ImageDraw.Draw(image)
    _centered_icon(draw, (mx, my + 14, mx + mw, my + 58), icon_name, font_icon_metric, METRICS_TEXT)
    _centered_text(draw, (mx, my + 62, mx + mw, my + 88), title, font_md, METRICS_TEXT)
    _centered_text(draw, (mx, my + 92, mx + mw, my + mh - 14), value, font_metric, METRICS_TEXT)

  # =========================================================================
  # PLACES PANEL
  # =========================================================================
  x0, y0, x1, y1 = PLACES_BOX
  panel_w, panel_h = _box_size(PLACES_BOX)
  _rounded_card(image, PLACES_BOX, CARD_TOP, CARD_BOTTOM)
  place_list = places or []
  place_colors = (PLACE_A, PLACE_B)
  place_area_h = panel_h - 2 * CARD_PAD
  ph = (place_area_h - INNER_GAP) // 2
  for index in range(2):
    place = place_list[index] if index < len(place_list) else {}
    py = y0 + CARD_PAD + index * (ph + INNER_GAP)
    px0 = x0 + CARD_PAD
    px1 = x1 - CARD_PAD
    color = place_colors[index]
    cell = Image.new("RGB", (px1 - px0, ph), color)
    mask = Image.new("L", (px1 - px0, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, px1 - px0 - 1, ph - 1), radius=RADIUS_INNER, fill=255)
    image.paste(cell, (px0, py), mask)
    ImageDraw.Draw(image, "RGBA").rounded_rectangle(
      (px0, py, px1, py + ph),
      radius=RADIUS_INNER,
      outline=(255, 177, 90, 60),
      width=1,
    )
    draw = ImageDraw.Draw(image)
    pname = place.get("name") or ("La Défense" if index == 0 else "Balard")
    period = place.get("period") or "—"
    _text(draw, (px0 + 14, py + 14), pname, font_h2)
    bb = draw.textbbox((0, 0), period, font=font_xs)
    bw = bb[2] - bb[0] + 20
    bx = px1 - 14 - bw
    draw.rounded_rectangle((bx, py + 16, bx + bw, py + 38), radius=10, fill=PRIMARY_SOFT)
    _text(draw, (bx + 10, py + 20), period, font_xs, METRICS_TEXT)

    _icon(draw, (px0 + 14, py + 66), "thermostat", font_icon_md, PRIMARY_SOFT)
    _text(
      draw,
      (px0 + 54, py + 70),
      f"{format_temperature(place.get('minimum'))} / {format_temperature(place.get('maximum'))}",
      font_metric,
    )
    rain_p = place.get("rain_probability")
    rain_txt = "—" if rain_p is None else f"{int(round(rain_p))}%"
    _icon(draw, (px0 + 14, py + 112), "humidity_percentage", font_icon_md, PRIMARY_SOFT)
    _text(draw, (px0 + 54, py + 116), rain_txt, font_metric)
    rw = draw.textbbox((0, 0), rain_txt, font=font_metric)
    _text(draw, (px0 + 62 + (rw[2] - rw[0]), py + 127), "de pluie", font_sm, MUTED)
    if place.get("error"):
      _text(draw, (px0 + 14, py + ph - 26), str(place["error"])[:36], font_xs, ERROR)

  # =========================================================================
  # HOURLY
  # =========================================================================
  x0, y0, x1, y1 = HOURLY_BOX
  panel_w, panel_h = _box_size(HOURLY_BOX)
  _rounded_card(image, HOURLY_BOX, CARD_TOP, CARD_BOTTOM)
  draw = ImageDraw.Draw(image)
  _text(draw, (x0 + CARD_PAD, y0 + CARD_PAD), "Prochaines heures", font_h2)
  hourly = (weather or {}).get("hourly") or []
  if hourly:
    n = min(12, len(hourly))
    area_x = x0 + CARD_PAD
    area_y = y0 + CARD_PAD + 40
    area_w = panel_w - 2 * CARD_PAD
    area_h = panel_h - CARD_PAD - 40 - CARD_PAD
    cell_gap = 10
    hw = (area_w - (n - 1) * cell_gap) // n
    for index, item in enumerate(hourly[:n]):
      hx = area_x + index * (hw + cell_gap)
      tile_y = area_y
      hy = tile_y + 16
      _inner_tile(image, (hx, tile_y, hx + hw, tile_y + area_h), (*CARD_INNER, 210))
      draw = ImageDraw.Draw(image)
      _centered_text(draw, (hx, hy, hx + hw, hy + 22), format_time(item.get("time"), timezone), font_sm, MUTED)
      _centered_icon(
        draw,
        (hx, hy + 36, hx + hw, hy + 78),
        weather_icon_name(item.get("weather_code")),
        font_icon_sm,
        PRIMARY_SOFT,
      )
      _centered_text(
        draw,
        (hx, hy + 84, hx + hw, hy + 114),
        format_temperature(item.get("temperature_2m")),
        font_card,
      )
      _centered_text(
        draw,
        (hx, tile_y + area_h - 34, hx + hw, tile_y + area_h - 10),
        f"{int(round(item.get('precipitation_probability') or 0))}% pluie",
        font_xs,
        MUTED,
      )

  # =========================================================================
  # DAILY
  # =========================================================================
  x0, y0, x1, y1 = DAILY_BOX
  panel_w, panel_h = _box_size(DAILY_BOX)
  _rounded_card(image, DAILY_BOX, CARD_TOP, CARD_BOTTOM)
  draw = ImageDraw.Draw(image)
  _text(draw, (x0 + CARD_PAD, y0 + CARD_PAD), "7 prochains jours", font_h2)
  daily = ((weather or {}).get("daily") or [])[1:8]
  if daily:
    n = min(7, len(daily))
    area_x = x0 + CARD_PAD
    area_y = y0 + CARD_PAD + 40
    area_w = panel_w - 2 * CARD_PAD
    area_h = panel_h - CARD_PAD - 40 - CARD_PAD
    cell_gap = 10
    dw = (area_w - (n - 1) * cell_gap) // n
    for index, item in enumerate(daily[:n]):
      dx = area_x + index * (dw + cell_gap)
      dy = area_y
      _inner_tile(image, (dx, dy, dx + dw, dy + area_h), (*CARD_INNER, 210))
      draw = ImageDraw.Draw(image)
      _centered_text(draw, (dx, dy + 16, dx + dw, dy + 40), format_day(item.get("time"), timezone), font_md, MUTED)
      _centered_icon(
        draw,
        (dx, dy + 40, dx + dw, dy + 86),
        weather_icon_name(item.get("weather_code")),
        font_icon_sm,
        PRIMARY_SOFT,
      )
      temps = (
        f"{format_temperature(item.get('temperature_2m_min')).replace("C", "")} / "
        f"{format_temperature(item.get('temperature_2m_max')).replace("C", "")}"
      )
      _centered_text(draw, (dx, dy + 102, dx + dw, dy + 130), temps, font_card)
      _centered_text(
        draw,
        (dx, dy + area_h - 34, dx + dw, dy + area_h - 10),
        f"{int(round(item.get('precipitation_probability_max') or 0))}% pluie",
        font_xs,
        MUTED,
      )

  # =========================================================================
  # PLUS — lever/coucher + blague
  # =========================================================================
  x0, y0, x1, y1 = PLUS_BOX
  panel_w, panel_h = _box_size(PLUS_BOX)
  _rounded_card(image, PLUS_BOX, CARD_TOP, CARD_BOTTOM)
  draw = ImageDraw.Draw(image)

  sun_y = y0 + CARD_PAD
  sun_h = 100
  sun_w = (panel_w - 2 * CARD_PAD - INNER_GAP) // 2
  for index, (title, value, icon_name) in enumerate((
    ("Lever", format_clock_time(focus_day.get("sunrise"), timezone), "wb_twilight"),
    ("Coucher", format_clock_time(focus_day.get("sunset"), timezone), "wb_twilight_2"),
  )):
    sx = x0 + CARD_PAD + index * (sun_w + INNER_GAP)
    _inner_tile(image, (sx, sun_y, sx + sun_w, sun_y + sun_h), (*CARD_INNER, 210))
    draw = ImageDraw.Draw(image)
    _icon(draw, (sx + sun_w - 80, sun_y + 12), icon_name, font_icon_lg_plus, PRIMARY_SOFT)
    _text(draw, (sx + 12, sun_y + 22), title, font_xs, MUTED)
    _text(draw, (sx + 12, sun_y + 42), value, font_card)

  joke_left = x0 + CARD_PAD
  joke_width = panel_w - 2 * CARD_PAD
  joke_area_top = sun_y + sun_h + 16
  joke_area_bottom = y1 - CARD_PAD
  if joke:
    setup = joke.get("joke") or ""
    answer = joke.get("answer") or ""
    # Setup vers le milieu de la zone, réponse collée en bas à droite
    joke_top = joke_area_top + max((joke_area_bottom - joke_area_top - 90) // 3, 8)
    _wrap_text(
      draw,
      setup,
      (joke_left, joke_top),
      joke_width,
      font_joke,
      PRIMARY_SOFT,
      max_lines=3,
      line_gap=26,
      align="left",
    )
    if answer:
      _wrap_text(
        draw,
        answer,
        (joke_left, joke_area_bottom - 28),
        joke_width,
        font_md,
        TEXT,
        max_lines=2,
        line_gap=22,
        align="right",
      )
  else:
    _text(draw, (joke_left, joke_area_top + 20), "Chargement de la blague…", font_md, MUTED)

  return image
