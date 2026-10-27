# Verificación final (actividad 12)

Corrida local del 21 de octubre de 2026, rama `sprint-aptitudes`:

| Comando | Resultado |
|---|---|
| `npm test` | 11 de 11 pruebas pasan |
| `npm run build` | Build correcto (JS 211 kB, 66 kB comprimido) |
| `python -m pytest -q` | 48 de 48 pruebas pasan |
| `python backend/validar_datos.py` | `OK: 8 aptitudes, 24 preguntas, 20 vacantes` |
| `git grep` y `git log -p` buscando llaves privadas, tokens de DuckDNS y contraseñas | Ninguno; no hay `.pem`, `.key` ni `.env` rastreados |

## Rúbrica y evidencia

| Criterio | Evidencia en el repositorio | Evidencia que falta (personas) |
|---|---|---|
| 1. Infraestructura y NGINX (30) | `deploy/nginx/pulso.conf` (HTTPS, redirección 80→443, `limit_req`, sin exponer Ollama), `deploy/nodo0_nginx.sh`, `deploy/nodo0_ufw.sh` (22, 80, 443, 8080, `tailscale0` con temporizador de rescate), `deploy/vm_ufw.sh`, `deploy/vm_ollama_localhost.sh`, diagrama en el README | Ejecutar los scripts y capturar los puntos 1 a 11, 15, 16 y 19 de `deploy/checklist_evidencias.md` |
| 2. App e integración IA (30) | `backend/ia.py` (Ollama `/api/chat` + tools `calcular_afinidad` y `obtener_vacante`), `backend/apoyo.py` (uso del dataset), `backend/main.py`, pantallas en `src/`, pruebas `test_api.py` y `test_apoyo.py` | Captura de una explicación real con «Generada con IA» y de `verificar_ollama.sh`; captura de Antigravity |
| 3. SCRUM y trabajo en equipo (15) | Commits por actividad (`feat(act-N)`), `documentacion/scrum.md` | Ramas por rol con commits de cada integrante desde su computadora; capturas del tablero; retrospectiva |
| 4. Negocio y documentación (15) | `README.md` con diagrama de red Mermaid y configuración del proxy, `documentacion/idea_de_negocio.md` | Exportar la idea de negocio a PDF de 1 página; nombres del equipo en el README |
| 5. Despliegue y demo (10) | `deploy/README.md`, `deploy/pulso.service`, `documentacion/guion_video.md` | Desplegar en la VM, probar desde celular con datos móviles y grabar el video de 2 a 3 minutos |

## Casos de la sección 9 del plan

| Qué se prueba | Cómo | Resultado |
|---|---|---|
| Motor, cálculo del perfil | `test_pregunta_invertida`, `test_opcion_multiple_y_promedio`, `test_evaluar_devuelve_perfil_y_5_recomendaciones` | Pasa |
| Motor, afinidad | `test_afinidad_ejemplo_resuelto` | Pasa: 89 %, fortalezas A1 y A3, brecha A6 |
| Motor, sentido de las recomendaciones | 3 perfiles en `test_motor.py` | Pasa. Técnico: V02, V01, V04, V03, V08. Servicio: V13, V15, V20, V19, V07. Equilibrado (55 en todo): todas entre 85 y 99 |
| API, datos inválidos | 8 casos en `test_evaluar_rechaza_datos_invalidos_con_error_claro` + JSON mal formado | Pasa: `422` con mensaje en español y el servicio sigue arriba |
| IA, calidad | 5 casos reales con el modelo | **Pendiente** (requiere la VM con Ollama) |
| IA, tool calling | `test_explicacion_con_tool_calling` con Ollama simulado | Pasa: el modelo no recibe números en el prompt; los obtiene por la tool |
| IA, respaldo | `test_explicar_con_ollama_apagado_usa_plantilla`, `test_porcentaje_equivocado_usa_plantilla`, `test_modelo_sin_soporte_de_tools_usa_plantilla` | Pasa |
| Tiempo de respuesta | Medir `POST /api/explicar` en la VM | **Pendiente**; límite fijado en 120 s (`OLLAMA_TIMEOUT` y `proxy_read_timeout`) |
| Celular | Capturas a 375 px de ancho de inicio, resultados, detalle y apoyo (navegador sin interfaz) | Se ve bien; tabla de requisitos ajustada. **Pendiente** en 2 celulares reales |
| Acceso desde fuera | Celular con datos móviles hacia `https://TU_SUBDOMINIO.duckdns.org` | **Pendiente** |
| Seguridad básica | Ollama en `127.0.0.1`, UFW en la VM, `curl` al 11434 desde fuera | Configurado; **pendiente** de comprobar |
| Privacidad | Logs de uvicorn en la corrida local | Solo rutas y códigos; ningún texto. `test_no_registra_el_texto_en_logs` pasa; NGINX con `access_log off` en `/api/apoyo` |
| Módulo de apoyo | `test_apoyo.py`: entrevista, texto sin relación, crisis en español y en inglés, longitud | Pasa |

## Despliegue final (21 de octubre de 2026, noche)

| Comprobación | Resultado |
|---|---|
| `https://mentalhealth-app.duckdns.org/api/salud` desde Internet | `{"ok":true}` |
| `/api/salud/ollama` desde Internet | `{"ok":true,"modelo":"granite4.2:3b"}` |
| Flujo completo por la URL pública (prueba, 5 vacantes, «¿Por qué?», apoyo) | Funciona; «¿Por qué?» con IA y tools en 30 s |
| `granite4.2:3b` real en 6 vacantes | 6 de 6 con IA y tool, 17 a 42 s, porcentajes iguales al motor |
| `nginx -t` en `nodo0` | Correcto; solo el sitio `pulso` activo |
| UFW en `nodo0` | Activo (22, 80, 443, 8080, `tailscale0`, `wg0`, 51820/udp, 41641/udp); temporizador cancelado |
| `systemctl status pulso` en la VM | `active (running)`, habilitado al arranque |
| 11434 y 8000 desde Internet | Sin respuesta |
| Límite de peticiones | 429 desde la segunda petición seguida a `/api/explicar` |

El reporte con capturas está en el documento compartido «Reporte final: Pulso · IA e infraestructura de red».
