# Meteo Getter — kiosk Pi Zero 2W

Application **Python** plein écran 1080p (Pillow + pygame), sans navigateur ni bureau.

## Prérequis

- Raspberry Pi Zero 2W
- Raspberry Pi OS **Lite** 64-bit (recommandé)
- Wi‑Fi + HDMI 1080p
- Boot en **console** (pas le desktop Pixel)

## Installation

```bash
# Copier ce dossier pi/ sur le Pi, puis :
cd /home/VOTRE_USER/meteo-getter/pi
chmod +x install.sh
sudo ./install.sh
```

Renseignez le token blagues (optionnel) :

```bash
nano .env
# BLAGUES_API_TOKEN=votre_token
sudo systemctl restart meteo-getter
```

## Commandes utiles

```bash
sudo systemctl status meteo-getter
journalctl -u meteo-getter -f
sudo systemctl stop meteo-getter
```

Test manuel (depuis une console graphique ou avec écran DRM) :

```bash
cd /home/VOTRE_USER/meteo-getter/pi
python3 main.py
# développement PC :
python3 main.py --windowed
```

## Boot console

```bash
sudo raspi-config
# System Options → Boot / Auto Login → Console (ou Console autologin)
```

## HDMI 1080p

Si l’écran n’est pas détecté correctement, dans `/boot/firmware/config.txt` (ou `/boot/config.txt`) :

```text
hdmi_group=1
hdmi_mode=16
```

Puis redémarrez.

## Contenu affiché

- Météo Open-Meteo (ville + pluie 5 min + heures + semaine)
- Deux lieux (La Défense, Balard)
- Blague (Blagues API) si token présent
- Refresh météo toutes les 60 s ; blague toutes les 3 h
- Cache local dans `~/.cache/meteo-getter/`

## Configuration

Éditez [`config.py`](config.py) pour changer `LOCATION`, `PLACES` ou `SCREEN` (1920×1080 par défaut).
