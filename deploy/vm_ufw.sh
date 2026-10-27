#!/usr/bin/env bash
# Firewall de la VM cliente. Correr con: sudo bash deploy/vm_ufw.sh
# - 8000 (app) solo desde la VPN (interfaz tailscale0).
# - 11434 (Ollama) cerrado para todos: la app lo usa por localhost.
set -euo pipefail

ufw allow 22/tcp                                   # SSH (quítalo si no entras por SSH a la VM)
ufw allow in on tailscale0 to any port 8000 proto tcp
ufw deny 8000/tcp
ufw deny 11434/tcp
ufw default deny incoming
ufw default allow outgoing
ufw --force enable
ufw status verbose

echo
echo "OJO: si Ollama corre en Docker con '-p 11434:11434', Docker se salta UFW."
echo "Corre deploy/vm_ollama_localhost.sh para publicarlo solo en 127.0.0.1."
