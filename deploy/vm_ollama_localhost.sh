#!/usr/bin/env bash
# Deja Ollama escuchando SOLO en localhost y arrancando con la VM.
# Correr con: sudo bash deploy/vm_ollama_localhost.sh
# Los modelos no se pierden: están en el volumen ollama_data.
set -euo pipefail

if docker ps -a --format '{{.Names}}' | grep -qx ollama; then
  echo "Ollama en Docker. Puertos actuales:"; docker port ollama || true
  if ! docker inspect ollama --format '{{range .Mounts}}{{.Name}} {{end}}' | grep -qw ollama_data; then
    echo "ALTO: los modelos no están en el volumen ollama_data; no se recrea el contenedor."
    docker inspect ollama --format '{{json .Mounts}}'; exit 1
  fi
  docker stop ollama && docker rm ollama
  docker run -d --name ollama --restart unless-stopped \
    -p 127.0.0.1:11434:11434 -v ollama_data:/root/.ollama ollama/ollama
  sleep 3
  echo "Puertos nuevos (debe decir 127.0.0.1:11434):"; docker port ollama
  docker exec ollama ollama list
else
  echo "Ollama instalado sin Docker (servicio systemd)."
  if [ -f /etc/systemd/system/ollama.service.d/override.conf ]; then
    echo "Hay un override; revisa que NO tenga OLLAMA_HOST=0.0.0.0:"; cat /etc/systemd/system/ollama.service.d/override.conf
  fi
  systemctl enable --now ollama
fi

echo; echo "Escucha en:"; ss -tlnp | grep 11434
curl -s -m 5 http://localhost:11434/api/tags | head -c 300; echo
