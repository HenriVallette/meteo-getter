# Projet : Meteo Getter

## Objectif

**Meteo Getter** est un service ultra-léger qui interroge l’API de Météo-France pour récupérer et afficher :

- la **pluie dans l’heure**,
- les **températures prévues sur la journée**,
- les **températures prévues sur la semaine**.

Le projet est conçu **sans framework** afin de réduire au maximum la consommation de ressources et de stockage, avec un objectif clair : tourner efficacement sur un **Raspberry Pi Zero (8 Go)**.

---

## Fonctionnalités principales

- Récupération périodique des données météo via l’API Météo-France.
- Extraction des informations utiles pour l’affichage :
  - intensité/probabilité de pluie à court terme,
  - températures horaires (ou demi-journées) pour la journée,
  - tendances de température sur 7 jours.
  - utilisation du modèle AROME pour la pluie dans l'heure et les infos proches dans le temps
  - utilisation du modèle ARPEGE pour la météo des prochains jours

---

## Contraintes techniques

Le projet suit une approche **minimaliste et embarquée** :

- **Aucun framework** (front ou back) pour limiter la taille binaire et les dépendances.
- Dépendances externes réduites au strict nécessaire.
- Logs simples et rotation légère pour préserver le stockage.
- Format de données compact (JSON brut + normalisation locale).
- Architecture pensée pour un matériel à faibles ressources (CPU/RAM/IO).

---

## Cycle de récupération des données

1. Déclenchement d’un cycle (timer).
2. Appel à l’API Météo-France.
3. Validation et normalisation des champs utiles.
4. Mise en cache locale des dernières données valides.
5. Mise à disposition des données pour l’affichage.

En cas d’erreur réseau/API :
- conservation de la dernière valeur valide,
- nouveau retry au cycle suivant,
- limitation des appels pour éviter la surcharge.

---

## Données exploitées

### 1) Pluie dans l’heure
- horizon très court terme,
- niveau/plage de précipitations,
- information prioritaire pour l’alerte immédiate.

### 2) Températures de la journée
- température prévue par plage horaire,
- min/max et évolution dans la journée.

### 3) Températures de la semaine
- vue synthétique des prochains jours,
- tendance générale (hausse/baisse/stabilité),
- min/max journaliers.

---

## Performance et sobriété (Raspberry Pi Zero)

Pour garantir une exécution fluide sur un Pi Zero :

- fréquence d’appel bornée à 2min,
- parsing ciblé uniquement sur les données nécessaires,
- cache local en mémoire (et persistance optionnelle légère),
- pas de couche applicative lourde ni surcouche d’abstraction inutile.

Résultat : un service météo fiable, compact et peu coûteux en ressources.

---

## Évolutions possibles

- mode “éco” (rafraîchissement adaptatif selon l’heure ou la météo),
- alertes locales (notification pluie imminente),
- export des historiques (CSV/JSON),
- interface d’affichage simplifiée e-ink / écran LCD.

---

## Résumé

Meteo Getter est un projet orienté **efficacité** : récupérer l’essentiel de la météo Météo-France, l’exploiter rapidement, et l’afficher de manière utile, tout en restant **léger, maintenable et compatible avec un Raspberry Pi Zero 8 Go**.
