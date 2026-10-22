"""Libellés FR pour les codes météo WMO (Open-Meteo)."""

WEATHER_CODES = {
  0: "Ciel dégagé",
  1: "Plutôt dégagé",
  2: "Partiellement nuageux",
  3: "Couvert",
  45: "Brouillard",
  48: "Brouillard givrant",
  51: "Bruine légère",
  53: "Bruine",
  55: "Bruine forte",
  56: "Bruine verglaçante",
  57: "Forte bruine verglaçante",
  61: "Pluie légère",
  63: "Pluie",
  65: "Forte pluie",
  66: "Pluie verglaçante",
  67: "Forte pluie verglaçante",
  71: "Neige légère",
  73: "Neige",
  75: "Forte neige",
  77: "Grains de neige",
  80: "Averses légères",
  81: "Averses",
  82: "Fortes averses",
  85: "Averses de neige",
  86: "Fortes averses de neige",
  95: "Orage",
  96: "Orage avec grêle",
  99: "Fort orage avec grêle",
}


def get_weather_label(code: int | None) -> str:
  if code is None:
    return "Temps indéterminé"
  return WEATHER_CODES.get(int(code), "Temps indéterminé")
