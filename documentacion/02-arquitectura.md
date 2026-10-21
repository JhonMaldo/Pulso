# Arquitectura

## Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `src/main.jsx` | Interfaz, formularios, navegación, estado de sesión, historial, impresión y descarga |
| `src/model.js` | Catálogo de aptitudes, preguntas, plantillas, validación, puntuaciones y búsqueda del dataset |
| `src/styles.css` | Diseño adaptable, controles y estilos de impresión |
| `src/KnowledgePanel.jsx` | Consulta interactiva bilingüe, selección de temas y comparación con el original |
| `src/knowledge.js` | Unión de traducciones por etiqueta e índice y recuperación de información |
| `src/data/KB_es.json` | Traducciones parciales y resúmenes identificados de las 79 intenciones |
| `KB_limpio.json` | Dataset original importado por Vite, sin modificaciones |
| `tests/model.test.js` | Pruebas del cálculo y recuperación de ejemplos reales |
| `index.html` | Entrada HTML y metadatos en español |

## Flujo de datos

Empresa + vacantes → respuestas a la encuesta → `evaluate(answers, jobs)` → reporte con copia de empresa, respuestas y perfiles de vacantes → consulta, descarga o impresión.

Dataset original + traducciones → `buildKnowledge(source, spanish)` → catálogo de 79 temas → `findKnowledge(entries, query)` → selección del tema → respuesta en español, ejemplo y texto original. Este camino no comparte consultas con el cálculo de afinidad ni el reporte. El módulo y el dataset se cargan bajo demanda al abrir la consulta; Vite genera archivos separados.

El estado de React mantiene empresa, borrador de vacante, vacantes, candidato, respuestas, consentimiento, reporte e historial. Cada reporte contiene su propia copia de empresa, pesos y respuestas. Cambiar la configuración después no recalcula evaluaciones anteriores. Crear una nueva evaluación reinicia respuestas, nombre y consentimiento.

## Ejecución y almacenamiento

Vite sirve el cliente durante desarrollo y genera `dist/` para alojamiento estático. No existen endpoints, credenciales, llamadas a modelos ni servidor de aplicación. El dataset se incluye en el cliente y es visible para quien abra el sitio. No colocar información confidencial en él.

No se utiliza localStorage ni sessionStorage. Recargar elimina el estado; el borrado explícito lo reinicia. La descarga JSON incluye nombre o alias, empresa y respuestas, por lo que debe tratarse como un archivo personal. El diálogo de impresión depende del navegador. Las fuentes de Google Fonts son el único recurso externo de presentación; si no cargan se usan fuentes alternativas.

La consulta puede abrirse desde la encuesta sin reiniciar las respuestas, el alias o el consentimiento. El texto consultado permanece únicamente en el componente de consulta y se descarta al salir. No existe una llamada a servicios de traducción o a modelos externos.
