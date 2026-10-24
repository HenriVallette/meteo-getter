"""Affichage plein écran : pygame (KMS/DRM ou fenêtré), sinon framebuffer /dev/fb0."""

from __future__ import annotations

import array
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from config import SCREEN, SCREEN_HEIGHT, SCREEN_WIDTH

# fcntl = Unix uniquement (mode graphique tty / framebuffer Pi)
try:
  import fcntl
except ImportError:  # Windows
  fcntl = None  # type: ignore[assignment]

if TYPE_CHECKING:
  from PIL import Image

# Backends : "pygame" | "fb"
_backend: Optional[str] = None
_screen = None
_clock = None
_last_surface = None
_actual_size = SCREEN
_fb = None
_tty_fd: Optional[int] = None

KDSETMODE = 0x4B3A
KD_GRAPHICS = 1
KD_TEXT = 0


def _ensure_xdg_runtime_dir() -> None:
  """Mesa/EGL (kmsdrm) exige un XDG_RUNTIME_DIR accessible en écriture."""
  if sys.platform == "win32" or not hasattr(os, "getuid"):
    return

  current = os.environ.get("XDG_RUNTIME_DIR", "")
  if current and os.path.isdir(current) and os.access(current, os.W_OK):
    return

  uid = os.getuid()
  for path in (Path(f"/run/user/{uid}"), Path(f"/tmp/runtime-meteo-{uid}")):
    try:
      path.mkdir(mode=0o700, parents=True, exist_ok=True)
      if os.access(path, os.W_OK):
        os.environ["XDG_RUNTIME_DIR"] = str(path)
        return
    except OSError:
      continue


def _prepare_video_env(fullscreen: bool) -> None:
  if sys.platform == "win32":
    if not os.environ.get("SDL_VIDEODRIVER"):
      os.environ["SDL_VIDEODRIVER"] = "windows"
    return

  _ensure_xdg_runtime_dir()
  if not os.environ.get("DISPLAY"):
    os.environ.pop("WAYLAND_DISPLAY", None)
    os.environ.setdefault("EGL_PLATFORM", "drm")
    os.environ.setdefault("SDL_FBDEV", "/dev/fb0")

  if os.environ.get("SDL_VIDEODRIVER"):
    return
  if fullscreen and not os.environ.get("DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"


def _read_sysfs_int(path: str, default: int = 0) -> int:
  try:
    return int(Path(path).read_text(encoding="ascii").strip())
  except (OSError, ValueError):
    return default


def _enter_graphics_mode() -> None:
  """Empêche la console texte d'écraser le framebuffer (Linux uniquement)."""
  global _tty_fd
  if fcntl is None:
    return
  for tty in ("/dev/tty1", "/dev/tty0", "/dev/console"):
    try:
      fd = os.open(tty, os.O_RDWR)
      fcntl.ioctl(fd, KDSETMODE, KD_GRAPHICS)
      _tty_fd = fd
      return
    except OSError:
      continue


def _leave_graphics_mode() -> None:
  global _tty_fd
  if _tty_fd is None or fcntl is None:
    return
  try:
    fcntl.ioctl(_tty_fd, KDSETMODE, KD_TEXT)
  except OSError:
    pass
  try:
    os.close(_tty_fd)
  except OSError:
    pass
  _tty_fd = None


class _Framebuffer:
  """Backend sans EGL : écriture directe sur /dev/fb0."""

  def __init__(self, device: str = "/dev/fb0") -> None:
    if not Path(device).exists():
      raise FileNotFoundError(f"{device} introuvable")

    size_raw = Path("/sys/class/graphics/fb0/virtual_size").read_text(encoding="ascii").strip()
    width_s, height_s = size_raw.split(",")
    self.width = int(width_s)
    self.height = int(height_s)
    self.bpp = _read_sysfs_int("/sys/class/graphics/fb0/bits_per_pixel", 32)
    self.stride = _read_sysfs_int(
      "/sys/class/graphics/fb0/stride",
      self.width * max(self.bpp // 8, 1),
    )
    self.device = device
    self._fp = open(device, "r+b", buffering=0)

    # Désactive le blanking si possible
    try:
      Path("/sys/class/graphics/fb0/blank").write_text("0", encoding="ascii")
    except OSError:
      pass

  @property
  def size(self) -> tuple[int, int]:
    return (self.width, self.height)

  def show(self, image: "Image.Image") -> None:
    from PIL import Image as PilImage

    if image.size != (self.width, self.height):
      image = image.resize((self.width, self.height), PilImage.Resampling.LANCZOS)
    if image.mode != "RGB":
      image = image.convert("RGB")

    if self.bpp == 16:
      raw = _rgb_to_rgb565(image)
    elif self.bpp == 24:
      raw = image.tobytes("raw", "BGR")
    else:
      # 32 bpp : BGRX (courant sur Pi / DRM fbdev)
      raw = image.tobytes("raw", "BGRX")

    expected = self.stride * self.height
    if len(raw) < expected and self.stride == self.width * (self.bpp // 8):
      self._fp.seek(0)
      self._fp.write(raw)
    elif len(raw) == expected:
      self._fp.seek(0)
      self._fp.write(raw)
    else:
      # stride > width * bpp : copie ligne par ligne
      px = self.bpp // 8
      row = self.width * px
      self._fp.seek(0)
      for y in range(self.height):
        start = y * row
        self._fp.write(raw[start : start + row])
        pad = self.stride - row
        if pad > 0:
          self._fp.write(b"\x00" * pad)
    self._fp.flush()

  def close(self) -> None:
    try:
      self._fp.close()
    except OSError:
      pass


def _rgb_to_rgb565(image: "Image.Image") -> bytes:
  pixels = image.tobytes()
  out = array.array("H")
  for i in range(0, len(pixels), 3):
    r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
    out.append(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))
  if sys.byteorder != "little":
    out.byteswap()
  return out.tobytes()


def _init_pygame(fullscreen: bool) -> None:
  global _backend, _screen, _clock, _actual_size

  _prepare_video_env(fullscreen)
  import pygame

  driver = os.environ.get("SDL_VIDEODRIVER", "(défaut)")
  runtime = os.environ.get("XDG_RUNTIME_DIR", "")
  print(f"[display] tentative pygame driver={driver} XDG_RUNTIME_DIR={runtime}", flush=True)

  pygame.display.init()
  pygame.font.init()

  if fullscreen and not os.environ.get("DISPLAY"):
    _screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
  else:
    flags = pygame.FULLSCREEN if fullscreen else 0
    _screen = pygame.display.set_mode(SCREEN, flags)

  _actual_size = _screen.get_size()
  pygame.display.set_caption("Meteo Getter")
  pygame.mouse.set_visible(False)
  _clock = pygame.time.Clock()
  _backend = "pygame"
  print(f"[display] pygame OK surface={_actual_size[0]}x{_actual_size[1]}", flush=True)


def _init_framebuffer() -> None:
  global _backend, _fb, _actual_size

  print("[display] fallback framebuffer /dev/fb0 (sans EGL)", flush=True)
  _enter_graphics_mode()
  _fb = _Framebuffer("/dev/fb0")
  _actual_size = _fb.size
  _backend = "fb"
  print(f"[display] fb0 OK surface={_actual_size[0]}x{_actual_size[1]} bpp={_fb.bpp}", flush=True)


def init_display(fullscreen: bool = True) -> None:
  """Initialise l'affichage. Sur Pi Lite : pygame/kmsdrm, sinon /dev/fb0."""
  use_fb_first = os.environ.get("METEO_DISPLAY", "").lower() == "fb"

  if sys.platform == "win32" or os.environ.get("DISPLAY") or not fullscreen:
    _init_pygame(fullscreen=fullscreen)
    return

  if use_fb_first:
    _init_framebuffer()
    return

  try:
    _init_pygame(fullscreen=True)
    return
  except Exception as error:  # noqa: BLE001
    print(f"[display] pygame/kmsdrm échoué: {error}", flush=True)
    try:
      import pygame
      pygame.display.quit()
    except Exception:
      pass
    os.environ.pop("SDL_VIDEODRIVER", None)

  try:
    _init_framebuffer()
  except Exception as error:  # noqa: BLE001
    raise RuntimeError(
      "[Service Meteo] Impossible d'ouvrir l'écran (pygame EGL et /dev/fb0 en échec). "
      f"Détail: {error}. "
      "Installez libegl-dev, vérifiez HDMI et : ls -l /dev/fb0 /dev/dri/"
    ) from error


def _poll_quit_pygame() -> bool:
  import pygame

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return False
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
      return False
  return True


def show_image(image: "Image.Image") -> bool:
  """Affiche l'image. Retourne False pour quitter."""
  global _last_surface

  if _backend is None:
    init_display()

  if _backend == "fb":
    assert _fb is not None
    _fb.show(image)
    return True

  import pygame

  target_w, target_h = _actual_size
  if image.size != (target_w, target_h):
    image = image.resize((target_w, target_h))

  surface = pygame.image.frombuffer(image.tobytes(), image.size, image.mode).convert()
  _last_surface = surface
  _screen.blit(surface, (0, 0))
  pygame.display.flip()
  if _clock is not None:
    _clock.tick(10)
  return _poll_quit_pygame()


def wait_with_events(timeout_ms: int) -> bool:
  """Attend timeout_ms. False = quitter."""
  if _backend == "fb":
    time.sleep(timeout_ms / 1000.0)
    return True

  import pygame

  elapsed = 0
  step = 100
  while elapsed < timeout_ms:
    if _last_surface is not None and _screen is not None:
      _screen.blit(_last_surface, (0, 0))
      pygame.display.flip()
    if not _poll_quit_pygame():
      return False
    pygame.time.wait(step)
    elapsed += step
  return True


def shutdown() -> None:
  global _backend, _screen, _fb, _last_surface

  if _backend == "fb":
    if _fb is not None:
      _fb.close()
      _fb = None
    _leave_graphics_mode()
  else:
    try:
      import pygame
      pygame.quit()
    except Exception:
      pass

  _backend = None
  _screen = None
  _last_surface = None
  sys.stdout.flush()
