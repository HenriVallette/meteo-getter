const WEATHER_CODES = {
  0: { icon: "sunny", label: "Ciel dégagé" },
  1: { icon: "partly_cloudy_day", label: "Plutôt dégagé" },
  2: { icon: "partly_cloudy_day", label: "Partiellement nuageux" },
  3: { icon: "cloud", label: "Couvert" },
  45: { icon: "foggy", label: "Brouillard" },
  48: { icon: "foggy", label: "Brouillard givrant" },
  51: { icon: "rainy_light", label: "Bruine légère" },
  53: { icon: "rainy_light", label: "Bruine" },
  55: { icon: "rainy", label: "Bruine forte" },
  56: { icon: "weather_hail", label: "Bruine verglaçante" },
  57: { icon: "weather_hail", label: "Forte bruine verglaçante" },
  61: { icon: "rainy_light", label: "Pluie légère" },
  63: { icon: "rainy", label: "Pluie" },
  65: { icon: "rainy_heavy", label: "Forte pluie" },
  66: { icon: "weather_hail", label: "Pluie verglaçante" },
  67: { icon: "weather_hail", label: "Forte pluie verglaçante" },
  71: { icon: "weather_snowy", label: "Neige légère" },
  73: { icon: "weather_snowy", label: "Neige" },
  75: { icon: "snowing_heavy", label: "Forte neige" },
  77: { icon: "weather_snowy", label: "Grains de neige" },
  80: { icon: "rainy_light", label: "Averses légères" },
  81: { icon: "rainy", label: "Averses" },
  82: { icon: "rainy_heavy", label: "Fortes averses" },
  85: { icon: "weather_snowy", label: "Averses de neige" },
  86: { icon: "snowing_heavy", label: "Fortes averses de neige" },
  95: { icon: "thunderstorm", label: "Orage" },
  96: { icon: "thunderstorm", label: "Orage avec grêle" },
  99: { icon: "thunderstorm", label: "Fort orage avec grêle" }
};

export function getWeatherDescription(code) {
  return WEATHER_CODES[code] ?? { icon: "cloud", label: "Temps indéterminé" };
}

export function createWeatherIcon(code, className = "") {
  const description = getWeatherDescription(code);
  const icon = document.createElement("span");

  icon.className = `material-symbols-outlined ${className}`.trim();
  icon.textContent = description.icon;
  icon.setAttribute("aria-label", description.label);
  icon.title = description.label;
  return icon;
}

export function createRainItem(item, timezone, formatTime, formatNumber) {
  const precipitation = item.precipitation ?? item.rain ?? 0;
  const element = document.createElement("div");
  const time = document.createElement("span");
  const icon = document.createElement("span");
  const amount = document.createElement("span");

  element.className = "rain-item";
  time.className = "rain-time";
  time.textContent = formatTime(item.time, timezone);
  icon.className = "material-symbols-outlined rain-icon";
  icon.textContent = precipitation > 0 ? "rainy" : "water_drop";
  icon.setAttribute("aria-label", precipitation > 0 ? "Pluie prévue" : "Pas de pluie");
  amount.textContent = `${formatNumber(precipitation, 1)} mm`;
  element.append(time, icon, amount);
  return element;
}

export function createHourCard(item, timezone, formatTime, formatTemperature) {
  const element = document.createElement("article");
  const time = document.createElement("time");
  const temperature = document.createElement("strong");
  const rain = document.createElement("span");

  element.className = "hour-card";
  time.textContent = formatTime(item.time, timezone);
  temperature.textContent = formatTemperature(item.temperature_2m);
  rain.textContent = `${Math.round(item.precipitation_probability ?? 0)} % pluie`;
  element.append(time, createWeatherIcon(item.weather_code), temperature, rain);
  return element;
}

export function createDayCard(item, timezone, formatDay, formatTemperature) {
  const element = document.createElement("article");
  const day = document.createElement("time");
  const temperatures = document.createElement("strong");
  const rain = document.createElement("span");

  element.className = "day-card";
  day.textContent = formatDay(item.time, timezone);
  temperatures.textContent = `${formatTemperature(item.temperature_2m_min)} / ${formatTemperature(item.temperature_2m_max)}`;
  rain.textContent = `${Math.round(item.precipitation_probability_max ?? 0)} % pluie`;
  element.append(day, createWeatherIcon(item.weather_code), temperatures, rain);
  return element;
}