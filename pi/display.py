"""Affichage plein écran via pygame (KMS/DRM sur Pi Lite, fenêtré ailleurs)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from config import SCREEN, SCREEN_HEIGHT, SCREEN_WIDTH

if TYPE_CHECKING:
  from PIL import Image

_screen = None
_clock = None
_last_surface = None
_actual_size = SCREEN


def _ensure_xdg_runtime_dir() -> None:
  """Mesa/EGL (kmsdrm) exige un XDG_RUNTIME_DIR accessible en écriture."""
  current = os.environ.get("XDG_RUNTIME_DIR", "")
  if current and os.path.isdir(current) and os.access(current, os.W_OK):
    return

  uid = os.getuid()
  candidates = [
    Path(f"/run/user/{uid}"),
    Path(f"/tmp/runtime-meteo-{uid}"),
  ]
  for path in candidates:
    try:
      path.mkdir(mode=0o700, parents=True, exist_ok=True)
      if os.access(path, os.W_OK):
        os.environ["XDG_RUNTIME_DIR"] = str(path)
        return
    except OSError:
      continue


def _prepare_video_env(fullscreen: bool) -> None:
  """Prépare l'environnement SDL avant tout import/init pygame."""
  _ensure_xdg_runtime_dir()

  # Évite que SDL choisisse Wayland/X11 alors qu'il n'y a pas de session graphique
  if not os.environ.get("DISPLAY"):
    os.environ.pop("WAYLAND_DISPLAY", None)

  if os.environ.get("SDL_VIDEODRIVER"):
    return

  if sys.platform == "win32":
    os.environ["SDL_VIDEODRIVER"] = "windows"
  elif fullscreen and not os.environ.get("DISPLAY"):
    # Raspberry Pi OS Lite : pas de X, affichage direct via KMS/DRM
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"


def _open_screen(pygame, fullscreen: bool):
  """Ouvre la surface d'affichage (mode natif en fullscreen Pi)."""
  if fullscreen:
    # (0, 0) = résolution courante du connecteur HDMI — plus fiable que forcer 1080p
    return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
  return pygame.display.set_mode(SCREEN)


def init_display(fullscreen: bool = True) -> None:
  global _screen, _clock, _actual_size

  _prepare_video_env(fullscreen)

  import pygame

  driver = os.environ.get("SDL_VIDEODRIVER", "(défaut SDL)")
  runtime = os.environ.get("XDG_RUNTIME_DIR", "")
  print(f"[display] SDL_VIDEODRIVER={driver} XDG_RUNTIME_DIR={runtime}", flush=True)

  pygame.display.init()
  pygame.font.init()

  last_error: Exception | None = None
  try:
    _screen = _open_screen(pygame, fullscreen)
  except pygame.error as error:
    last_error = error
    # Si kmsdrm échoue, ne pas retomber sur X11/Wayland sans DISPLAY (même erreur EGL)
    if os.environ.get("SDL_VIDEODRIVER") == "kmsdrm":
      raise RuntimeError(
        "[Service Meteo] Impossible d'ouvrir l'écran via KMS/DRM (EGL). "
        f"Détail SDL: {error}. "
        "Vérifiez HDMI, XDG_RUNTIME_DIR, groupes video/render, "
        "et arrêtez getty@tty1 si besoin (sudo systemctl stop getty@tty1)."
      ) from error
    raise

  _actual_size = _screen.get_size()
  print(f"[display] surface={_actual_size[0]}x{_actual_size[1]}", flush=True)
  if last_error is None and _actual_size != SCREEN:
    print(
      f"[display] rendu interne {SCREEN_WIDTH}x{SCREEN_HEIGHT} → scale {_actual_size}",
      flush=True,
    )

  pygame.display.set_caption("Meteo Getter")
  pygame.mouse.set_visible(False)
  _clock = pygame.time.Clock()


def _poll_quit() -> bool:
  """Retourne False si l'utilisateur demande à quitter."""
  import pygame

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return False
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
      return False
  return True


def show_image(image: "Image.Image") -> bool:
  """Affiche l'image et traite les événements. Retourne False pour quitter."""
  import pygame

  global _screen, _last_surface
  if _screen is None:
    init_display()

  target_w, target_h = _actual_size
  if image.size != (target_w, target_h):
    image = image.resize((target_w, target_h))

  surface = pygame.image.frombuffer(image.tobytes(), image.size, image.mode).convert()
  _last_surface = surface
  _screen.blit(surface, (0, 0))
  pygame.display.flip()

  if _clock is not None:
    _clock.tick(10)
  return _poll_quit()


def wait_with_events(timeout_ms: int) -> bool:
  """Attend timeout_ms en gardant la fenêtre réactive. False = quitter."""
  import pygame

  elapsed = 0
  step = 100
  while elapsed < timeout_ms:
    if _last_surface is not None and _screen is not None:
      _screen.blit(_last_surface, (0, 0))
      pygame.display.flip()
    if not _poll_quit():
      return False
    pygame.time.wait(step)
    elapsed += step
  return True


def shutdown() -> None:
  try:
    import pygame
    pygame.quit()
  except Exception:
    pass
  sys.stdout.flush()
