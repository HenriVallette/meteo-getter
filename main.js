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

async function displayHours() {
  const container = document.getElementById("prevision-journaliere");
  container.innerHTML = "";
  for (let i = 10; i < 22; i++) {
    const heure = document.createElement("div");
    heure.classList.add("heure");
    heure.innerHTML = `
      <span>${i}:00</span>
      <span>${Math.floor(Math.random() * (25 - 15 + 1)) + 15}°C</span>
    `;
    container.appendChild(heure);
  }
}

async function displayDays() {
  const container = document.getElementById("prevision-semaine");
  container.innerHTML = "";
  const jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
  for (let i = 0; i < 7; i++) {
    const jour = document.createElement("div");
    jour.classList.add("jour");
    const temperature = Math.floor(Math.random() * (25 - 15 + 1)) + 15;
    const temperatureResentie = temperature + Math.floor(Math.random() * (5 - 1 + 1)) + 1;
    jour.innerHTML = `
      <span>${jours[i]}</span>
      <span>${temperature}°C</span>
      <span>${temperatureResentie}°C ressenti</span>
      <span>Aucune pluie</span>
    `;
    container.appendChild(jour);
  }
}

async function displayRainInTHeHour() {
  const container = document.getElementById("pluie-dans-l-heure");
  container.innerHTML = "";
  const timings = ['5min', '10min', '', '20min', '', '30min', '', '50min', ''];
  for (let i = 0; i < 9; i++) {
    const item = document.createElement("div");
    item.classList.add("pluie-dans-l-heure-item");
    item.innerHTML = `
      <span class="material-symbols-outlined">humidity_high</span>
      <span>${timings[i]}</span>
    `;
    container.appendChild(item);
  }
}

//fetchMeteo();
displayDays();
displayHours();
displayRainInTHeHour();