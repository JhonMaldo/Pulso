# Lista de comprobación con evidencia (para el video y el README)

Guarda una captura de cada punto en `documentacion/evidencias/` (sin llaves, tokens ni contraseñas en pantalla).

| # | Qué | Dónde | Comando o acción | Resultado esperado | Hecho |
|---|---|---|---|---|---|
| 1 | VPN | nodo0 y VM | `tailscale status` | `nodo0` y la VM sin `offline` | [ ] |
| 2 | Ping por la VPN | VM | `ping -c 3 100.64.0.2` | 0 % de pérdida | [ ] |
| 3 | Ping inverso | nodo0 | `tailscale ping IP_VPN_DE_LA_VM` | `pong` | [ ] |
| 4 | Headscale | nodo0 | `headscale nodes list` | VM `online` | [ ] |
| 5 | Ollama | VM | `sudo docker exec ollama ollama list` | Modelo instalado | [ ] |
| 6 | Ollama solo local | VM | `sudo ss -tlnp \| grep 11434` | `127.0.0.1:11434` | [ ] |
| 7 | App | VM | `systemctl status pulso` | `active (running)` | [ ] |
| 8 | NGINX | nodo0 | `nginx -t` | `syntax is ok` y `test is successful` | [ ] |
| 9 | Configuración | nodo0 | `cat /etc/nginx/sites-available/pulso` | `proxy_pass` a la VM por la VPN | [ ] |
| 10 | Salud desde Internet | cualquier PC | `curl https://TU_SUBDOMINIO.duckdns.org/api/salud` | `{"ok":true}` | [ ] |
| 11 | Ollama desde la app | cualquier PC | `curl https://TU_SUBDOMINIO.duckdns.org/api/salud/ollama` | `"ok":true` | [ ] |
| 12 | Flujo completo | celular con datos móviles (sin Wi-Fi) | Abrir la URL, contestar, ver 5 vacantes, «¿Por qué?» | Sale «Generada con IA» | [ ] |
| 13 | Respaldo de IA | VM | `sudo docker stop ollama`, pulsar «¿Por qué?» en otra vacante, luego `sudo docker start ollama` | Sale «Explicación automática» sin romperse | [ ] |
| 14 | Módulo de apoyo | celular | Escribir «Estoy nervioso por mi entrevista» | Respuesta del dataset en español | [ ] |
| 15 | 11434 cerrado | nodo0 y una PC fuera de la VPN | `curl -m 5 http://IP_VPN_DE_LA_VM:11434/api/tags` | No responde (timeout o rechazado) | [ ] |
| 16 | 8000 cerrado fuera de la VPN | PC en la misma red local que la VM | `curl -m 5 http://IP_LAN_DE_LA_VM:8000/api/salud` | No responde | [ ] |
| 17 | Límite de peticiones | cualquier PC | 10 veces seguidas `POST /api/explicar` | Algunas responden `429` | [ ] |
| 18 | Privacidad | VM | `journalctl -u pulso -n 50` | Solo rutas; ningún texto ni respuesta | [ ] |
| 19 | UFW nodo0 | nodo0 | `ufw status verbose` y `systemctl list-timers --all \| grep ufw` | `active` con 22, 80, 443, 8080, tailscale0; sin temporizador | [ ] |
| 20 | Antigravity | PC del equipo | Captura del proyecto abierto con Claude Code en su terminal | | [ ] |
