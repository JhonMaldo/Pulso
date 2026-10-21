# Dataset y metodología

## Dataset real

`KB_limpio.json` contiene un objeto con la propiedad `intents`. Cada intención incluye `tag`, `patterns` y `responses`. Hay 79 intenciones, relacionadas con salud y bienestar, saludos y conversaciones generales. El contenido está principalmente en inglés.

La aplicación utiliza el archivo original al abrir «Consulta en español». La capa `src/data/KB_es.json` contiene 128 frases traducidas y 79 respuestas traducidas o resumidas, con cobertura de las 79 intenciones. Cada entrada conserva `tag` y `sourceIndex`, de modo que `buildKnowledge` recupera el original desde `patterns` o `responses`. No se han traducido las 3,139 frases de entrada completas ni todas las respuestas del archivo.

La búsqueda admite español e inglés, normaliza acentos y mayúsculas, y prioriza un ejemplo exacto, después coincidencias de texto y, finalmente, una proporción de al menos 60 % de palabras significativas (mínimo dos) o coincidencias literales en respuestas. Ignora palabras muy comunes. Devuelve hasta ocho temas y solo abre automáticamente el primero cuando existe un ejemplo exacto. Las coincidencias parciales se presentan para que el usuario elija; la puntuación interna de búsqueda no representa confianza clínica ni afinidad laboral.

El usuario también puede seleccionar cualquier tema sin buscar. Cada resultado muestra una respuesta localizada, su tipo («Traducción» o «Resumen adaptado»), el original y su ubicación. Las respuestas extensas se resumen con esa etiqueta. Las afirmaciones del asistente original sobre su identidad o capacidades se identifican como citas, no como capacidades de Pulso. La cifra de `mental-health-fact` se identifica como no verificada y el duplicado de respuesta de `fact-10` se explica expresamente.

No es una conversación generativa, ni una herramienta diagnóstica. El contenido se muestra como información educativa del archivo proporcionado. Las consultas no entran en el reporte de candidatos, no cambian el cálculo de puestos y se descartan al salir del módulo.

No se encontró una declaración de licencia o procedencia en la estructura del archivo; conviene confirmar derechos y origen antes de redistribuirlo. No es un dataset de reclutamiento: no existen etiquetas de desempeño, puestos o aptitudes que permitan entrenar y validar un recomendador laboral. No se presentan métricas de precisión, ya que no existe un modelo entrenado ni un conjunto de validación para esa tarea.

## Encuesta de aptitudes

Se diseñaron 12 preguntas nuevas, independientes del dataset: dos por cada dimensión de comunicación, análisis, organización, trabajo en equipo, liderazgo y creatividad. Son autodeclaraciones de frecuencia con valores enteros de 1 a 5. Ninguna pregunta es invertida.

Cada respuesta se transforma con `normalizada = (respuesta - 1) × 25`. La puntuación de una aptitud es el promedio de sus dos respuestas normalizadas, redondeado al entero más cercano.

- 75–100: fortaleza.
- 50–74: en desarrollo.
- 0–49: área de mejora.

Estas categorías son decisiones de diseño académico y requieren validación. Si ninguna aptitud alcanza un umbral, se informa expresamente en lugar de asignar etiquetas artificialmente.

## Afinidad de puestos

Cada vacante tiene seis prioridades enteras entre 0 y 5. Cero significa que esa aptitud no interviene. Se exige al menos una prioridad positiva.

`afinidad = redondear(Σ(puntuación de aptitud × prioridad) / Σ(prioridades))`

Ejemplo: comunicación 75 con peso 3 y análisis 0 con peso 1, y el resto con peso 0: `(75 × 3 + 0 × 1) / 4 = 56.25`, que se muestra como 56/100.

El desglose muestra prioridades, puntuaciones y contribuciones individuales redondeadas a una décima. Por redondeo, su suma puede diferir ligeramente del total. Las vacantes se ordenan por afinidad descendente. Un empate se resuelve alfabéticamente para presentar un orden estable y se anuncia si afecta al primer lugar. El primer puesto es relativo al conjunto disponible: no implica que la persona cumpla un mínimo de competencia.

No se usan emociones, diagnósticos, opiniones sobre salud mental ni datos demográficos en la puntuación. La descripción del puesto se conserva como contexto y no se interpreta automáticamente. No se mide conocimiento técnico específico. Para una futura evaluación técnica deberán diseñarse preguntas y evidencias adicionales relacionadas con cada puesto.
