#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="meteo-getter.service"
SERVICE_SRC="${SCRIPT_DIR}/${SERVICE_NAME}"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Lancez avec sudo : sudo ./install.sh"
  exit 1
fi

TARGET_USER="${SUDO_USER:-pi}"
TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
if [[ -z "${TARGET_HOME}" ]]; then
  echo "Impossible de résoudre le home de ${TARGET_USER}"
  exit 1
fi

echo "==> Installation des paquets apt"
apt-get update
apt-get install -y python3-pil python3-pygame fonts-dejavu-core

echo "==> Droits d'exécution"
chmod +x "${SCRIPT_DIR}/main.py" "${SCRIPT_DIR}/install.sh"

if [[ ! -f "${SCRIPT_DIR}/.env" && -f "${SCRIPT_DIR}/.env.example" ]]; then
  cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
  chown "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/.env"
  echo "==> .env créé depuis .env.example (renseignez BLAGUES_API_TOKEN si besoin)"
fi

TARGET_UID="$(id -u "${TARGET_USER}")"

echo "==> Configuration systemd (${TARGET_USER}, uid=${TARGET_UID})"
tmpdir="$(mktemp -d)"
sed \
  -e "s|REPLACE_USER|${TARGET_USER}|g" \
  -e "s|REPLACE_DIR|${SCRIPT_DIR}|g" \
  -e "s|REPLACE_UID|${TARGET_UID}|g" \
  "${SERVICE_SRC}" > "${tmpdir}/${SERVICE_NAME}"
install -m 644 "${tmpdir}/${SERVICE_NAME}" "${SERVICE_DST}"
rm -rf "${tmpdir}"

# Runtime dir Mesa/EGL + cache utilisateur
install -d -m 700 -o "${TARGET_USER}" -g "${TARGET_USER}" "/run/user/${TARGET_UID}"
install -d -o "${TARGET_USER}" -g "${TARGET_USER}" "${TARGET_HOME}/.cache/meteo-getter"

# Le getty sur tty1 empêche souvent d'être DRM master
systemctl stop getty@tty1.service || true
systemctl disable getty@tty1.service || true

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo
echo "Installé."
echo "  Status : sudo systemctl status ${SERVICE_NAME}"
echo "  Logs   : journalctl -u ${SERVICE_NAME} -f"
echo
echo "Important : bootez en console (pas le bureau) :"
echo "  sudo raspi-config → System Options → Boot / Auto Login → Console"
echo
echo "HDMI 1080p si besoin dans /boot/firmware/config.txt :"
echo "  hdmi_group=1"
echo "  hdmi_mode=16"
