#!/usr/bin/env bash
# Pasos de administrador en la VM, en un solo comando:
#   sudo bash ~/Pulso/deploy/vm_instalar_root.sh
# 1) Ollama solo en localhost  2) servicio systemd de Pulso  3) UFW: 8000 solo desde la VPN
set -euo pipefail
USUARIO="${SUDO_USER:-alonso}"
DIR="/home/$USUARIO/Pulso"

echo "== 1. Ollama solo en 127.0.0.1"
bash "$DIR/deploy/vm_ollama_localhost.sh"

echo "== 2. Servicio pulso"
sed "s/USUARIO_VM/$USUARIO/g" "$DIR/deploy/pulso.service" > /etc/systemd/system/pulso.service
systemctl daemon-reload
systemctl enable --now pulso
sleep 3
systemctl --no-pager status pulso | head -5
curl -s -m 5 http://localhost:8000/api/salud; echo

echo "== 3. Firewall de la VM"
bash "$DIR/deploy/vm_ufw.sh"

echo "== Listo. Comprobación:"
ss -tlnp | grep -E ':8000|:11434'
