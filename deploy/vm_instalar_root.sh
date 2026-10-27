#!/usr/bin/env bash
# Pasos de administrador en la VM, en un solo comando:
#   sudo bash ~/Pulso/deploy/vm_instalar_root.sh
# 1) apaga el Ollama de Docker de la VM  2) servicio systemd de Pulso  3) UFW: 8000 solo desde la VPN
# Ollama corre en el Windows anfitrión con la GPU (127.0.0.1:11434); la VM lo alcanza por 10.0.2.2 (NAT de VirtualBox).
set -euo pipefail
USUARIO="${SUDO_USER:-alonso}"
DIR="/home/$USUARIO/Pulso"

echo "== 1. Ollama de Docker en la VM: ya no se usa; se detiene y no arranca solo (los modelos se conservan en el volumen)"
if docker ps -a --format '{{.Names}}' | grep -qx ollama; then
  docker update --restart no ollama
  docker stop ollama || true
fi
curl -s -m 5 http://10.0.2.2:11434/api/version && echo "  <- Ollama del anfitrión alcanzable"

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
