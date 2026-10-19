import {
  LOCATION,
  PLACES,
  fetchWeather,
  loadWeatherCache,
  saveWeatherCache,
  selectDailyForecast
} from "./logic.js";
import {
  renderLocation,
  renderPlaces,
  renderStatus,
  renderWeather,
  setLoading
} from "./visual_functions.js";

const REFRESH_INTERVAL_MS = 60 * 1000; // Toutes les minutes

let latestWeather = null;

const refreshButton = document.getElementById("refresh-button");

document.addEventListener("visibilitychange", handleVisibilityChange);

initialize();

async function initialize() {
  const cachedWeather = loadWeatherCache();

  if (refreshButton) {
    refreshButton.addEventListener("click", refreshWeather);
  }

  renderLocation(LOCATION);

  if (isWeatherForLocation(cachedWeather, LOCATION)) {
    latestWeather = cachedWeather;
    renderWeather(cachedWeather);
    renderStatus("Dernières données enregistrées, actualisation en cours.", "warning");
  }

  await refreshWeather();
  window.setInterval(refreshWeather, REFRESH_INTERVAL_MS);
}

async function refreshWeather() {
  setLoading(true);
  renderStatus(`Actualisation de la météo pour ${LOCATION.name}…`);
  const placesPromise = refreshPlaces();

  try {
    const weather = await fetchWeather(LOCATION);

    latestWeather = weather;
    saveWeatherCache(weather);
    renderWeather(weather);
    renderLocation(LOCATION);
    renderStatus("Données météo à jour.", "success");
  } catch (error) {
    const cachedWeather = loadWeatherCache();

    if (isWeatherForLocation(cachedWeather, LOCATION)) {
      latestWeather = cachedWeather;
      renderWeather(cachedWeather);
      renderStatus(
        `Service indisponible. Données enregistrées affichées (${error.message})`,
        "warning"
      );
    } else {
      renderStatus(`Impossible de charger la météo : ${error.message}`, "error");
    }
  } finally {
    await placesPromise;
    setLoading(false);
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

async function handleVisibilityChange() {
  if (
    document.visibilityState === "visible"
    && (!latestWeather || Date.now() - latestWeather.updatedAt >= REFRESH_INTERVAL_MS)
  ) {
    await refreshWeather();
  }
}

function isWeatherForLocation(weather, location) {
  return Boolean(
    weather?.location
    && Math.abs(weather.location.latitude - location.latitude) < 0.01
    && Math.abs(weather.location.longitude - location.longitude) < 0.01
  );
}
