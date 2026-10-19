import {
  createDayCard,
  createHourCard,
  createRainItem,
  createWeatherIcon,
  getWeatherDescription
} from "./weather_components.js";

const temperatureFormatter = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 1
});

export function renderWeather(weather) {
  renderCurrentWeather(weather);
  renderRain(weather);
  renderHourly(weather);
  renderDaily(weather);
  document.getElementById("last-update").textContent = formatUpdateTime(weather.updatedAt);
}

export function renderLocation(location) {
  const details = [location.admin1, location.country].filter(Boolean).join(", ");

  document.getElementById("location-name").textContent = location.name;
  document.getElementById("location-details").textContent = details;
}

export function setLoading(isLoading) {
  const loadingIcon = document.getElementById("loading-message");

  loadingIcon.hidden = !isLoading;
  const refreshButton = document.getElementById("refresh-button");
  if (refreshButton) {
    refreshButton.disabled = isLoading;
  }
}

export function renderStatus(message, status = "info") {
  const element = document.getElementById("application-status");

  element.textContent = message;
  element.dataset.status = status;
}

function renderCurrentWeather(weather) {
  const current = weather.current;
  const description = getWeatherDescription(current.weather_code);
  const iconContainer = document.getElementById("current-weather-icon");
  const today = weather.daily[0] ?? {};

  document.getElementById("current-temperature").textContent = formatTemperature(
    current.temperature_2m
  );
  document.getElementById("apparent-temperature").textContent =
    `${formatTemperature(current.apparent_temperature)} ressenti`;
  document.getElementById("current-weather-label").textContent = description.label;
  document.getElementById("wind-speed").textContent =
    `${formatNumber(current.wind_speed_10m)} km/h`;
  document.getElementById("temperature-min").textContent = formatTemperature(
    today.temperature_2m_min
  );
  document.getElementById("temperature-max").textContent = formatTemperature(
    today.temperature_2m_max
  );
  document.getElementById("uv-index").textContent = formatNumber(today.uv_index_max);
  document.getElementById("humidity").textContent =
    `${Math.round(current.relative_humidity_2m ?? 0)} %`;
  iconContainer.replaceChildren(createWeatherIcon(current.weather_code, "current-icon"));
}

function renderRain(weather) {
  const container = document.getElementById("rain-forecast");

  container.replaceChildren();

  if (weather.minutely.length === 0) {
    const unavailable = document.createElement("p");

    unavailable.className = "empty-message";
    unavailable.textContent = "Prévision à 15 minutes indisponible pour ce lieu.";
    container.appendChild(unavailable);
    return;
  }

  for (const item of weather.minutely) {
    container.appendChild(
      createRainItem(item, weather.timezone, formatTime, formatNumber)
    );
  }
}

function renderHourly(weather) {
  const container = document.getElementById("hourly-forecast");

  container.replaceChildren();

  for (const item of weather.hourly) {
    container.appendChild(
      createHourCard(item, weather.timezone, formatTime, formatTemperature)
    );
  }
}

function renderDaily(weather) {
  const container = document.getElementById("daily-forecast");

  container.replaceChildren();

  for (const item of weather.daily) {
    container.appendChild(
      createDayCard(item, weather.timezone, formatDay, formatTemperature)
    );
  }
}

function formatTemperature(value) {
  return value == null ? "—" : `${temperatureFormatter.format(value)} °C`;
}

function formatNumber(value, maximumFractionDigits = 1) {
  if (value == null) {
    return "—";
  }

  return new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits
  }).format(value);
}

function formatTime(timestamp, timezone) {
  return new Intl.DateTimeFormat("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone
  }).format(timestamp * 1000);
}

function formatDay(timestamp, timezone) {
  const day = new Intl.DateTimeFormat("fr-FR", {
    weekday: "short",
    timeZone: timezone
  }).format(timestamp * 1000);

  return day.charAt(0).toUpperCase() + day.slice(1);
}

function formatUpdateTime(timestamp) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(timestamp);
}