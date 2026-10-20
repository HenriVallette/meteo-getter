const WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast";
const BLAGUES_API_URL = "https://www.blagues-api.fr/api/random";
const WEATHER_CACHE_KEY = "meteo-getter.weather";
const JOKE_CACHE_KEY = "meteo-getter.joke";
const REQUEST_TIMEOUT_MS = 10000;
const JOKE_REFRESH_INTERVAL_MS = 3 * 60 * 60 * 1000;
const NEXT_DAY_HOUR = 21;
const FIVE_MINUTE_SECONDS = 5 * 60;
const FIFTEEN_MINUTE_SECONDS = 15 * 60;
const RAIN_HOUR_STEPS = 12;

// Token Bearer à récupérer sur https://www.blagues-api.fr/ (profil).
export const BLAGUES_API_TOKEN = "";

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

export const PLACES = Object.freeze([
  Object.freeze({
    id: "defense",
    name: "La Défense",
    latitude: 48.89201,
    longitude: 2.23803,
    timezone: "Europe/Paris"
  }),
  Object.freeze({
    id: "balard",
    name: "Balard",
    latitude: 48.83545,
    longitude: 2.27815,
    timezone: "Europe/Paris"
  })
]);

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
    forecast_days: 8,
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

export function selectDailyForecast(daily, timezone, now = new Date()) {
  const index = getHour(now, timezone) >= NEXT_DAY_HOUR ? 1 : 0;
  return daily[index] ?? null;
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
    ? toFiveMinuteRain(response.minutely_15, currentTimestamp)
    : [];

  return {
    location,
    timezone: response.timezone ?? location.timezone ?? "UTC",
    utcOffsetSeconds: response.utc_offset_seconds ?? 0,
    updatedAt: Date.now(),
    current: { ...response.current },
    hourly: hourlyItems,
    minutely: minutelyItems,
    daily: mapSeries(response.daily).slice(0, 8)
  };
}

export function saveWeatherCache(weather, storage = globalThis.localStorage) {
  writeJsonCache(WEATHER_CACHE_KEY, weather, storage);
}

export function loadWeatherCache(storage = globalThis.localStorage) {
  return readJsonCache(WEATHER_CACHE_KEY, storage);
}

export function isJokeCacheFresh(joke, now = Date.now()) {
  return Boolean(joke?.fetchedAt && now - joke.fetchedAt < JOKE_REFRESH_INTERVAL_MS);
}

export function saveJokeCache(joke, storage = globalThis.localStorage) {
  writeJsonCache(JOKE_CACHE_KEY, joke, storage);
}

export function loadJokeCache(storage = globalThis.localStorage) {
  return readJsonCache(JOKE_CACHE_KEY, storage);
}

export async function fetchJoke() {
  if (!BLAGUES_API_TOKEN) {
    throw new Error(
      "Token Blagues API manquant. Renseignez BLAGUES_API_TOKEN dans logic.js."
    );
  }

  const response = await fetchJson(
    `${BLAGUES_API_URL}?disallow=dark&disallow=limit`,
    {
      Authorization: `Bearer ${BLAGUES_API_TOKEN}`
    }
  );

  if (!response?.joke) {
    throw new Error("La réponse blague est incomplète.");
  }

  return {
    id: response.id,
    type: response.type,
    joke: response.joke,
    answer: response.answer ?? "",
    fetchedAt: Date.now()
  };
}

export { JOKE_REFRESH_INTERVAL_MS };

async function fetchJson(url, headers = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...headers
      },
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Le service distant a répondu avec le statut ${response.status}.`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Le service distant n'a pas répondu à temps.", { cause: error });
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function getHour(date, timezone) {
  const hour = new Intl.DateTimeFormat("en-GB", {
    hour: "numeric",
    hourCycle: "h23",
    timeZone: timezone
  }).formatToParts(date).find(part => part.type === "hour");

  return Number(hour?.value ?? 0);
}

// Open-Meteo cumule la pluie sur 15 minutes. Chaque cumul est réparti
// en trois pas de 5 minutes pour couvrir l'heure à venir.
function toFiveMinuteRain(series, currentTimestamp) {
  const intervals = mapSeries(series)
    .filter(item => item.time > currentTimestamp)
    .slice(0, RAIN_HOUR_STEPS / 3);

  return intervals.flatMap(item => {
    const windowStart = item.time - FIFTEEN_MINUTE_SECONDS;

    return [0, 1, 2].map(step => ({
      time: windowStart + step * FIVE_MINUTE_SECONDS,
      precipitation: splitFifteenMinuteAmount(item.precipitation),
      rain: splitFifteenMinuteAmount(item.rain)
    }));
  });
}

function splitFifteenMinuteAmount(value) {
  return value == null ? null : value / 3;
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
