const WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast";
const WEATHER_CACHE_KEY = "meteo-getter.weather";
const REQUEST_TIMEOUT_MS = 10000;

// Ville affichée par l'application.
// Modifier cette variable pour changer de ville.
export const LOCATION = Object.freeze({
  name: "Boulogne-Billancourt",
  latitude: 48.83545,
  longitude: 2.24128,
  admin1: "Île-de-France",
  country: "France",
  timezone: "Europe/Paris"
});

export function buildQueryString(parameters) {
  const searchParameters = new URLSearchParams();

  for (const [key, value] of Object.entries(parameters)) {
    searchParameters.set(key, Array.isArray(value) ? value.join(",") : String(value));
  }

  return searchParameters.toString();
}

export async function fetchWeather(location) {
  const parameters = {
    latitude: location.latitude,
    longitude: location.longitude,
    models: "best_match",
    timezone: "auto",
    timeformat: "unixtime",
    forecast_days: 7,
    forecast_minutely_15: 8,
    current: [
      "temperature_2m",
      "apparent_temperature",
      "relative_humidity_2m",
      "precipitation",
      "rain",
      "weather_code",
      "wind_speed_10m",
      "is_day"
    ],
    minutely_15: ["precipitation", "rain"],
    hourly: [
      "temperature_2m",
      "apparent_temperature",
      "relative_humidity_2m",
      "precipitation_probability",
      "precipitation",
      "rain",
      "weather_code",
      "wind_speed_10m"
    ],
    daily: [
      "weather_code",
      "temperature_2m_min",
      "temperature_2m_max",
      "apparent_temperature_min",
      "apparent_temperature_max",
      "uv_index_max",
      "precipitation_sum",
      "precipitation_probability_max"
    ]
  };
  const response = await fetchJson(`${WEATHER_API_URL}?${buildQueryString(parameters)}`);
  return normalizeWeatherResponse(response, location);
}

export function normalizeWeatherResponse(response, location) {
  if (!response.current || !response.hourly || !response.daily) {
    throw new Error("La réponse météo est incomplète.");
  }

  const currentTimestamp = response.current.time;
  const hourlyItems = mapSeries(response.hourly)
    .filter(item => item.time >= currentTimestamp)
    .slice(0, 12);
  const minutelyItems = response.minutely_15
    ? mapSeries(response.minutely_15)
      .filter(item => item.time >= currentTimestamp)
      .slice(0, 5)
    : [];

  return {
    location,
    timezone: response.timezone ?? location.timezone ?? "UTC",
    utcOffsetSeconds: response.utc_offset_seconds ?? 0,
    updatedAt: Date.now(),
    current: { ...response.current },
    hourly: hourlyItems,
    minutely: minutelyItems,
    daily: mapSeries(response.daily).slice(0, 7)
  };
}

export function saveWeatherCache(weather, storage = globalThis.localStorage) {
  writeJsonCache(WEATHER_CACHE_KEY, weather, storage);
}

export function loadWeatherCache(storage = globalThis.localStorage) {
  return readJsonCache(WEATHER_CACHE_KEY, storage);
}

async function fetchJson(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      headers: {
        Accept: "application/json"
      },
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Le service distant a répondu avec le statut ${response.status}.`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Le service météo n'a pas répondu à temps.", { cause: error });
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function mapSeries(series) {
  return (series.time ?? []).map((time, index) => {
    const item = { time };

    for (const [key, values] of Object.entries(series)) {
      if (key !== "time" && Array.isArray(values)) {
        item[key] = values[index];
      }
    }

    return item;
  });
}

function readJsonCache(key, storage) {
  try {
    const value = storage.getItem(key);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

function writeJsonCache(key, value, storage) {
  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    // Le stockage peut être désactivé par le navigateur sans bloquer l'application.
  }
}
