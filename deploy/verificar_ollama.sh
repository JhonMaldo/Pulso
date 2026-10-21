#!/usr/bin/env bash
# Comprueba Ollama en la VM cliente ANTES de la Fase 2. Solo lee, no cambia nada.
# Uso (en la VM):  bash deploy/verificar_ollama.sh [modelo]
# Por defecto prueba granite4.2:3b, el modelo del agente del clima del equipo.
set -u
MODELO="${1:-granite4.2:3b}"
URL="http://localhost:11434"

echo "== 1. Modelos instalados (ollama list) =="
if command -v docker >/dev/null && sudo docker ps --format '{{.Names}}' 2>/dev/null | grep -qx ollama; then
  echo "(Ollama corre en Docker, contenedor 'ollama')"
  sudo docker exec ollama ollama list
  echo "Puertos publicados por el contenedor:"; sudo docker port ollama
else
  ollama list
fi

echo; echo "== 2. API local (/api/tags) =="
curl -s -m 5 "$URL/api/tags" | head -c 600; echo

echo; echo "== 3. ¿En qué dirección escucha el 11434? Debe ser 127.0.0.1 =="
sudo ss -tlnp | grep 11434 || echo "Nada escucha en 11434"

echo; echo "== 4. Llamada de prueba a /api/chat con una tool (puede tardar) =="
INICIO=$(date +%s)
curl -s -m 180 "$URL/api/chat" -H 'Content-Type: application/json' -d @- <<JSON
{
  "model": "$MODELO",
  "stream": false,
  "think": false,
  "messages": [
    {"role": "system", "content": "Usa la herramienta calcular_afinidad para responder."},
    {"role": "user", "content": "¿Qué afinidad tengo con la vacante V01?"}
  ],
  "tools": [{"type": "function", "function": {
    "name": "calcular_afinidad",
    "description": "Calcula la afinidad entre la persona y una vacante",
    "parameters": {"type": "object", "required": ["vacante_id"],
      "properties": {"vacante_id": {"type": "string"}}}}}]
}
JSON
echo; echo "Tiempo: $(( $(date +%s) - INICIO )) s"
echo
echo "Qué buscar: en la respuesta debe aparecer \"tool_calls\" con \"calcular_afinidad\" y \"V01\"."
echo "Si dice 'does not support tools' o tarda más de 60 s, avisa: hay que cambiar de modelo."
