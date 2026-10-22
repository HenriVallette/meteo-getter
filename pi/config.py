"""Configuration de l'affichage kiosk Pi Zero 2W."""

from pathlib import Path

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
BLAGUES_API_URL = "https://www.blagues-api.fr/api/random"

REQUEST_TIMEOUT_S = 10
WEATHER_REFRESH_S = 60
JOKE_REFRESH_S = 3 * 60 * 60
NEXT_DAY_HOUR = 21
FIVE_MINUTE_SECONDS = 5 * 60
FIFTEEN_MINUTE_SECONDS = 15 * 60
RAIN_HOUR_STEPS = 12

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN = (SCREEN_WIDTH, SCREEN_HEIGHT)

CACHE_DIR = Path.home() / ".cache" / "meteo-getter"
WEATHER_CACHE_FILE = CACHE_DIR / "weather.json"
JOKE_CACHE_FILE = CACHE_DIR / "joke.json"
PLACES_CACHE_FILE = CACHE_DIR / "places.json"

ENV_FILE = Path(__file__).resolve().parent / ".env"

LOCATION = {
  "name": "Boulogne-Billancourt",
  "latitude": 48.83545,
  "longitude": 2.24128,
  "admin1": "Île-de-France",
  "country": "France",
  "timezone": "Europe/Paris",
}

PLACES = (
  {
    "id": "defense",
    "name": "La Défense",
    "latitude": 48.89201,
    "longitude": 2.23803,
    "timezone": "Europe/Paris",
  },
  {
    "id": "balard",
    "name": "Balard",
    "latitude": 48.83545,
    "longitude": 2.27815,
    "timezone": "Europe/Paris",
  },
)
