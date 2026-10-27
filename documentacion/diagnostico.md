# Diagnóstico inicial (Fase 0, actividades 0 y 1)

Fecha: miércoles 21 de octubre de 2026. Entrega: viernes 23 de octubre de 2026.

Fuentes leídas: PDF de la práctica, `plan_replanteado_aptitudes_vacantes.md` (plan vigente), `Reporte-Servidor-nodo0.md`, `Reporte_Docker_Ollama_Clima_Agente.md` (tool personalizado de Ollama) y el repositorio completo.

## 1. Qué hay hoy en el repositorio

| Pieza | Archivo | Estado | ¿Se reutiliza? |
|---|---|---|---|
| App React 19 + Vite 6, solo frontend | `src/main.jsx` (un solo componente grande) | Funciona: empresa, vacantes, autoevaluación, resultados, consulta | Sí: estructura de pestañas, barra de progreso, tarjetas, tablas, banner de resultado, avisos |
| Estilos | `src/styles.css` | Cuidado, adaptado a celular y a impresión | Sí, completo |
| Lógica de cálculo | `src/model.js` | 6 aptitudes, 12 preguntas en escala, promedio ponderado en el navegador | No: el cálculo pasa al backend (`motor.py`). Se conserva `normalize` |
| Búsqueda en el dataset | `src/knowledge.js` | Búsqueda por palabras en inglés y español | La idea sí; la búsqueda pasa al backend con TF-IDF |
| Traducciones del dataset | `src/data/KB_es.json` | 79 temas, 128 frases y 79 respuestas en español, con `sourceIndex` al original | Sí: el backend las usa para comparar en español y responder en español |
| Panel de consulta | `src/KnowledgePanel.jsx` | Consulta del dataset sin filtro de temas | Se reemplaza por el módulo "Apoyo en la búsqueda de empleo" |
| Pruebas | `tests/model.test.js`, `tests/knowledge.test.js` (`node --test`) | Pasan con el modelo de 6 aptitudes | `knowledge.test.js` sigue sirviendo; `model.test.js` se reescribe |
| Dataset | `KB_limpio.json` | 79 tags, 3,139 frases, casi todo en inglés | Sí, solo para el módulo de apoyo |
| Documentación | `documentacion/01` a `04`, `README.md` | Describe el prototipo de 6 aptitudes | Se reemplaza por la nueva |

Detalle: el `package-lock.json` subido no traía las dependencias de Vite; se corrigió con `npm install` (commit `chore(act-0)`).

## 2. Diferencia entre lo que hay y el plan

| Tema | Hoy | Plan vigente |
|---|---|---|
| Aptitudes | 6 (Comunicación, Análisis, Organización, Equipo, Liderazgo, Creatividad) | 8 (A1 a A8) |
| Preguntas | 12, todas en escala 1 a 5 | 16 a 24, opción múltiple (A1, A2, A3, A6, A7) y escala (A4, A5, A8), algunas invertidas |
| Vacantes | Las captura el usuario con 4 plantillas | Catálogo `vacantes.json` de 20 vacantes con mínimos y pesos |
| Fórmula | Promedio ponderado del perfil | `cumplimiento = min(perfil/mínimo, 1)` ponderado; fortalezas y brechas por mínimo |
| Dónde se calcula | Navegador | `motor.py` detrás de una API FastAPI |
| IA | Ninguna | Ollama con tool calling (`/api/chat` + `tools`) y plantilla de respaldo |
| Dataset | Consulta libre de todos los temas | Módulo de apoyo con tags filtrados, TF-IDF, umbral y protocolo de crisis |
| Publicación | Local (`127.0.0.1:5173`) | NGINX en `nodo0` → VPN → VM cliente `:8000` |
| Datos personales | Nombre del candidato obligatorio, historial de sesión | Alias opcional, nada se guarda |

## 3. Rúbrica: qué se cumple y qué falta

| Criterio (puntos) | Ya se cumple | Falta |
|---|---|---|
| 1. Infraestructura y NGINX (30) | Headscale 0.29.4 activo, `nodo0` `online`, NGINX + Certbot descritos en el Entregable 1 | Apuntar NGINX a la app (hoy apunta a `danielserv`, apagada → 502), `limit_req`, UFW con 80/443/8080, VM `online`, evidencia y documentación |
| 2. App e integración IA (30) | App React funcional; dataset cargado | Motor con API, Ollama + Tool respondiendo, uso del dataset con sentido (módulo de apoyo), evidencia de Antigravity |
| 3. SCRUM y trabajo en equipo (15) | Repositorio en GitHub | Commits distribuidos por integrante, ramas por rol, tablero y retrospectiva (`scrum.md`) |
| 4. Negocio y documentación (15) | Documentación del prototipo | README nuevo con diagrama de red, `idea_de_negocio.md` (1 cuartilla, a PDF) |
| 5. Despliegue y demo (10) | Nada en la nube | App en la VM publicada por NGINX y video de 2 a 3 minutos |

## 4. Módulo "Apoyo en la búsqueda de empleo"

- Backend `apoyo.py` carga `KB_limpio.json` y `src/data/KB_es.json` (las traducciones ya existentes; se resuelven por `sourceIndex`, igual que `buildKnowledge`).
- Solo usa los tags permitidos: `problem`, `stressed`, `anxious`, `scared`, `sad`, `worthless`, `depressed`, `sleep`, `no-approach`, `learn-more`, `meditation`, `user-advice`, `help`, `fact-*` y `suicide`.
- Arma un índice TF-IDF (implementado en Python puro, sin `scikit-learn`, para no cargar la VM) con las frases en inglés y las traducciones al español, normalizadas como `normalize()` del frontend (sin acentos, minúsculas). Se agregan unas cuantas frases semilla en español sobre la búsqueda de empleo para el tag `problem` (entrevistas, rechazo, despido), marcadas como agregadas por el equipo.
- Similitud coseno contra cada frase; gana la mejor. Si es menor al umbral, devuelve un mensaje general y no inventa.
- Responde en español con la traducción existente del tag; si el tag no tiene traducción, con un mensaje general.
- Crisis: si el tag es `suicide` o el texto contiene "quitarme la vida", "suicid", "no quiero vivir" o "matarme", siempre devuelve la Línea de la Vida (del dataset) y el 911.
- No se guarda, no se registra en logs, no toca el perfil y no aparece en resultados.

## 5. Tool personalizado de Ollama

No está en el repositorio. Está documentado en `Reporte_Docker_Ollama_Clima_Agente.md` (`agente_clima_conagua.py`): Ollama en Docker en la VM, modelo `granite4.2:3b`, `/api/chat` con `tools`, `think: false`, el programa ejecuta la función pedida y devuelve un mensaje `role: "tool"` con `tool_name`. `ia.py` sigue ese mismo patrón con `calcular_afinidad` y `obtener_vacante`, usando `httpx` para poder fijar el límite de espera (el SDK del reporte se colgaba sin timeout).

**Riesgo detectado:** en ese reporte Ollama corre con `docker run -p 11434:11434`, que publica el puerto en todas las interfaces y **Docker se salta UFW**. En el despliegue se cambia a `-p 127.0.0.1:11434:11434`.

## 6. Estructura de carpetas propuesta

```
Pulso/
├── index.html, package.json, vite.config.js   frontend React (raíz)
├── src/                                        pantallas
│   ├── main.jsx, api.js, Prueba.jsx, Resultados.jsx, Apoyo.jsx, styles.css
│   └── data/KB_es.json, ejemplo_*.json         traducciones y JSON de ejemplo
├── tests/                                      pruebas del frontend (node --test)
├── KB_limpio.json                              dataset del profesor
├── backend/
│   ├── main.py, motor.py, ia.py, apoyo.py, validar_datos.py
│   ├── datos/preguntas.json, datos/vacantes.json
│   ├── tests/
│   ├── requirements.txt, .env.example
├── deploy/
│   ├── pulso.service, nginx/pulso.conf
│   ├── vm_preparar.md, nodo0_ufw.sh, vm_ufw.sh, verificar_ollama.sh
│   └── checklist_evidencias.md
└── documentacion/                              diagnóstico, negocio, guion, scrum
```

## 7. Datos por confirmar (no se inventan)

| Dato | Lo que sabemos | Estado |
|---|---|---|
| VM con Ollama | Según el reporte del servidor, `alonso` `100.64.0.1`, `offline` desde el 8 oct | Por confirmar con `tailscale ip -4` |
| SO, RAM, núcleos de la VM | Ubuntu con Python 3.14, 4 GB, 4 núcleos (reporte del agente) | Por confirmar |
| Modelo | `granite4.2:3b` (reporte del agente); `qwen2.5-coder:1.5b` en `danielserv` | Por confirmar con `ollama list` |
| Subdominio DuckDNS | No aparece en ningún documento | Se usa `TU_SUBDOMINIO` |
| Hora y formato de entrega | No aparece | Pendiente |
| Integrantes y roles | Usuarios de Headscale: alonso, daniel, Jhony/Jhon, Fabrizio | Pendiente |
