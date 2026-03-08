const url = "https://api.open-meteo.com/v1/forecast";

const params = {
  latitude: 48.8355,
  longitude: 2.2413,
  daily: ["apparent_temperature_min", "apparent_temperature_max", "temperature_2m_min", "temperature_2m_max", "uv_index_max"],
  hourly: ["rain", "apparent_temperature", "weather_code", "sunshine_duration", "relative_humidity_2m", "precipitation", "temperature_20m", "wind_speed_20m", "temperature_50m", "wind_speed_50m", "cape"],
  models: "meteofrance_seamless",
  current: ["temperature_2m", "rain", "is_day", "apparent_temperature"],
  minutely_15: "rain",
  start_date: "2026-03-08",
  end_date: "2026-03-13",
};

function buildQueryString(params) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      searchParams.set(key, value.join(","));
    } else {
      searchParams.set(key, String(value));
    }
  }
  return searchParams.toString();
}

async function fetchMeteo() {
  const queryString = buildQueryString(params);
  const fullUrl = `${url}?${queryString}`;

  try {
    const response = await fetch(fullUrl);
    if (!response.ok) {
      throw new Error(`Erreur HTTP : ${response.status}`);
    }
    const data = await response.json();
    console.log("Réponse API :", data);
    document.getElementById("result").textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    console.error("Erreur API :", error);
    document.getElementById("result").textContent = `Erreur : ${error.message}`;
  }
}

fetchMeteo();