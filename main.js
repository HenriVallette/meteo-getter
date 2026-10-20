import {
  JOKE_REFRESH_INTERVAL_MS,
  LOCATION,
  PLACES,
  fetchJoke,
  fetchWeather,
  isJokeCacheFresh,
  loadJokeCache,
  loadWeatherCache,
  saveJokeCache,
  saveWeatherCache,
  selectDailyForecast
} from "./logic.js";
import {
  renderJoke,
  renderLocation,
  renderPlaces,
  renderWeather
} from "./visual_functions.js";

const REFRESH_INTERVAL_MS = 60 * 1000; // Toutes les minutes

let latestWeather = null;
let latestJoke = null;

const refreshButton = document.getElementById("refresh-button");

document.addEventListener("visibilitychange", handleVisibilityChange);

initialize();

async function initialize() {
  const cachedWeather = loadWeatherCache();
  const cachedJoke = loadJokeCache();

  if (refreshButton) {
    refreshButton.addEventListener("click", refreshWeather);
  }

  renderLocation(LOCATION);

  if (isWeatherForLocation(cachedWeather, LOCATION)) {
    latestWeather = cachedWeather;
    renderWeather(cachedWeather);
  }

  if (cachedJoke) {
    latestJoke = cachedJoke;
    renderJoke(cachedJoke);
  }

  await Promise.all([refreshWeather(), refreshJoke()]);
  window.setInterval(refreshWeather, REFRESH_INTERVAL_MS);
}

async function refreshWeather() {
  const placesPromise = refreshPlaces();

  try {
    const weather = await fetchWeather(LOCATION);

    latestWeather = weather;
    saveWeatherCache(weather);
    renderWeather(weather);
    renderLocation(LOCATION);
  } catch (error) {
    const cachedWeather = loadWeatherCache();

    if (isWeatherForLocation(cachedWeather, LOCATION)) {
      latestWeather = cachedWeather;
      renderWeather(cachedWeather);
    }
  } finally {
    await placesPromise;
  }
}

async function refreshPlaces() {
  const places = await Promise.all(PLACES.map(async place => {
    try {
      const weather = await fetchWeather(place);
      const forecast = selectDailyForecast(weather.daily, weather.timezone);

      return {
        id: place.id,
        period: !forecast
          ? "—"
          : forecast === weather.daily[0] ? "Aujourd'hui" : "Demain",
        minimum: forecast?.temperature_2m_min,
        maximum: forecast?.temperature_2m_max,
        rainProbability: forecast?.precipitation_probability_max,
        error: forecast ? "" : "Prévision du lendemain indisponible."
      };
    } catch (error) {
      return {
        id: place.id,
        period: "—",
        error: error.message
      };
    }
  }));

  renderPlaces(places);
}

async function refreshJoke(force = false) {
  const cachedJoke = latestJoke ?? loadJokeCache();

  if (!force && isJokeCacheFresh(cachedJoke)) {
    latestJoke = cachedJoke;
    renderJoke(cachedJoke);
    scheduleNextJokeRefresh();
    return;
  }

  try {
    const joke = await fetchJoke();

    latestJoke = joke;
    saveJokeCache(joke);
    renderJoke(joke);
    scheduleNextJokeRefresh(JOKE_REFRESH_INTERVAL_MS);
  } catch (error) {
    if (cachedJoke) {
      latestJoke = cachedJoke;
      renderJoke(cachedJoke, error.message);
    } else {
      renderJoke(null, error.message);
    }

    scheduleNextJokeRefresh(JOKE_REFRESH_INTERVAL_MS);
  }
}

function scheduleNextJokeRefresh(delay) {
  if (scheduleNextJokeRefresh.timeoutId) {
    window.clearTimeout(scheduleNextJokeRefresh.timeoutId);
  }

  const nextDelay = delay ?? (() => {
    const joke = latestJoke ?? loadJokeCache();
    const elapsed = joke?.fetchedAt ? Date.now() - joke.fetchedAt : JOKE_REFRESH_INTERVAL_MS;
    return Math.max(0, JOKE_REFRESH_INTERVAL_MS - elapsed);
  })();

  scheduleNextJokeRefresh.timeoutId = window.setTimeout(() => {
    refreshJoke(true);
  }, nextDelay);
}

async function handleVisibilityChange() {
  if (document.visibilityState !== "visible") {
    return;
  }

  const tasks = [];

  if (!latestWeather || Date.now() - latestWeather.updatedAt >= REFRESH_INTERVAL_MS) {
    tasks.push(refreshWeather());
  }

  if (!isJokeCacheFresh(latestJoke ?? loadJokeCache())) {
    tasks.push(refreshJoke());
  }

  if (tasks.length > 0) {
    await Promise.all(tasks);
  }
}

function isWeatherForLocation(weather, location) {
  return Boolean(
    weather?.location
    && Math.abs(weather.location.latitude - location.latitude) < 0.01
    && Math.abs(weather.location.longitude - location.longitude) < 0.01
  );
}
