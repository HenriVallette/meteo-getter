function getCurrentPosition(options = {}) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("La géolocalisation n'est pas supportée par ce navigateur."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      position => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        });
      },
      error => {
        reject(error);
      },
      options
    );
  });
}

getCurrentPosition()
  .then(async coords => {
    console.log("Coordonnées actuelles :", coords);
    res = await fetchMeteo(coords.latitude, coords.longitude);
    console.log(res);
  })
  .catch(err => {
    console.error("Erreur lors de la récupération des coordonnées GPS :", err);
  });

// Pour espace vide
// durée ensoleilement
// date / heure / fête / jour férié
// blague du jour
// connexion google agenda
// temps trajet taff



//fetchMeteo();
// setInterval(() => {
//   showLoadingMessage();
//   setTimeout(() => {
//     displayDays();
//     displayHours();
//     displayRainInTheHour();
//     hideLoadingMessage();
//   }, 1000);
// }, 5000);
displayDays();
displayHours();
displayRainInTheHour();
getCurrentPosition();