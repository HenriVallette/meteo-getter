"""Affichage plein écran via pygame."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from config import SCREEN, SCREEN_HEIGHT, SCREEN_WIDTH

if TYPE_CHECKING:
  from PIL import Image

_screen = None
_clock = None
_last_surface = None


def init_display(fullscreen: bool = True) -> None:
  global _screen, _clock

  # Sur Pi Lite sans X, privilégier KMS/DRM ; sous bureau laisser le défaut.
  if not os.environ.get("DISPLAY") and not os.environ.get("SDL_VIDEODRIVER"):
    os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")

  import pygame

  pygame.init()
  pygame.mouse.set_visible(False)
  flags = pygame.FULLSCREEN if fullscreen else 0
  try:
    _screen = pygame.display.set_mode(SCREEN, flags)
  except pygame.error:
    if os.environ.get("SDL_VIDEODRIVER") == "kmsdrm":
      os.environ.pop("SDL_VIDEODRIVER", None)
      pygame.display.quit()
      pygame.display.init()
    _screen = pygame.display.set_mode(SCREEN)
  pygame.display.set_caption("Meteo Getter")
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

  if image.size != (SCREEN_WIDTH, SCREEN_HEIGHT):
    image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT))

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
