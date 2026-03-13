async function showLoadingMessage() {
  document.getElementById("loading-message").classList.remove("hidden");
}

async function hideLoadingMessage() {
  document.getElementById("loading-message").classList.add("hidden");
}

async function displayHours() {
  const container = document.getElementById("prevision-journaliere");
  container.innerHTML = "";
  const currentHour = new Date().getHours();
  for (let i = currentHour; i < currentHour + 12; i++) {
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
  const currentDay = new Date().getDay();
  const jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
  for (let i = currentDay; i < currentDay + 7; i++) {
    const jour = document.createElement("div");
    jour.classList.add("jour");
    const temperature = Math.floor(Math.random() * (25 - 15 + 1)) + 15;
    const temperatureResentie = temperature + Math.floor(Math.random() * (5 - 1 + 1)) + 1;
    jour.innerHTML = `
      <span>${jours[i % 7]}</span>
      <span>${temperature}°C</span>
      <span>${temperatureResentie}°C ressenti</span>
      <span>Aucune pluie</span>
    `;
    container.appendChild(jour);
  }
}

async function displayRainInTheHour() {
  const container = document.getElementById("pluie-dans-l-heure");
  container.innerHTML = "";
  const timings = ['5min', '10min', '', '20min', '', '30min', '', '50min', ''];
  for (let i = 0; i < 9; i++) {
    const item = document.createElement("div");
    item.classList.add("pluie-dans-l-heure-item");
    if (i % 4 === 0) {
      item.innerHTML = getSmallRainItemComponent(timings[i]);
    } else if (i % 4 === 1) {
      item.innerHTML = getModerateRainItemComponent(timings[i]);
    } else if (i % 4 === 2) {
      item.innerHTML = getHeavyRainItemComponent(timings[i]);
    } else {
      item.innerHTML = getNoRainItemComponent(timings[i]);
    }
    container.appendChild(item);
  }
}