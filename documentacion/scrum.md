# SCRUM: backlog, Sprints y retrospectiva

## Product Backlog

| Prioridad | Historia de usuario | Estado |
|---|---|---|
| Debe | Como candidato quiero contestar una prueba corta para conocer mis aptitudes | Hecho |
| Debe | Como candidato quiero ver mi perfil en una gráfica para entender mis fortalezas | Hecho |
| Debe | Como candidato quiero ver las 5 vacantes que mejor encajan, con su porcentaje | Hecho |
| Debe | Como candidato quiero saber por qué me recomiendan una vacante y qué puedo mejorar | Hecho (IA + plantilla) |
| Debe | Como equipo queremos publicar el sistema con NGINX a través de la VPN | Archivos listos; falta ejecutar |
| Debería | Como candidato quiero apoyo emocional durante mi búsqueda sin que afecte mis resultados | Hecho (módulo de apoyo) |
| Debería | Como reclutador quiero ver el catálogo de vacantes y sus requisitos | API lista (`GET /api/vacantes`); sin pantalla |
| Podría | Como candidato quiero descargar mi resultado en PDF | Recortado |
| Podría | Como candidato quiero contar mi experiencia en texto libre y ver mis habilidades detectadas | Recortado |
| Podría | Como administrador quiero agregar vacantes desde un formulario | Recortado |

## Sprints

### Sprint 1: Cimientos (miércoles 21)

**Meta:** contratos acordados, datos listos, motor v1 probado, infraestructura base y esqueleto de pantallas.

| Rol | Tareas | Actividad | Rama |
|---|---|---|---|
| 1 | Acuerdos de arranque, diagnóstico, backlog y tablero | 0, 1 | `rol1-docs` |
| 2 | Revisar y ajustar `preguntas.json` (borrador de 24 preguntas) | 2 | `rol2-contenido` |
| 3 | Revisar `vacantes.json` con el rol 2; motor con pruebas | 3, 4 | `rol3-datos-ia` |
| 4 | Encender la VM, Headscale, `verificar_ollama.sh`, `/api/salud` por NGINX | 5 | `rol4-backend-infra` |
| 5 | Esqueleto de pantallas con datos de ejemplo | 6 | `rol5-frontend` |

### Sprint 2: Construcción (jueves 22)

**Meta:** flujo completo funcionando en el servidor: prueba, perfil, 5 vacantes y explicación con Ollama.

| Rol | Tareas | Actividad |
|---|---|---|
| 1 | Reunión de integración del mediodía; revisión y congelamiento por la noche | — |
| 2 | Textos finales y aviso de uso; versión final de `preguntas.json` | 11 |
| 3 | Probar el prompt y las tools con 5 casos; medir tiempo | 8 |
| 4 | API en la VM como servicio, NGINX a la app real, UFW | 7, 10 |
| 5 | Pantallas conectadas a la API real; prueba en 2 celulares | 9 |

### Sprint 3: Cierre (viernes 23, sin funciones nuevas)

**Meta:** pruebas, documentación, ensayo y entrega.

| Rol | Tareas | Actividad |
|---|---|---|
| Todos | Casos de prueba de la sección 9; corregir solo errores graves | 12 |
| 1 con 4 | README, diagrama, evidencias, idea de negocio en PDF | 13 |
| Todos | Ensayo de la demo, grabación del video, entrega | 14 |

## Tablero

Tres columnas: Por hacer, En proceso, Hecho. Guardar una captura al final de cada Sprint en `documentacion/evidencias/`.

| Sprint | Captura del tablero | Revisión hecha |
|---|---|---|
| 1 | _(pendiente)_ | [ ] |
| 2 | _(pendiente)_ | [ ] |
| 3 | _(pendiente)_ | [ ] |

## Retrospectiva

Llenar en 5 minutos al final de cada Sprint.

| Sprint | Qué salió bien | Qué mejorar | Acción para el siguiente |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 (final) | | | |

**Qué falta (con más tiempo):** validar las preguntas con un especialista, vacantes reales, pantalla de catálogo para reclutadores, HTTPS también en Headscale, política de acceso (ACL) en la VPN.
