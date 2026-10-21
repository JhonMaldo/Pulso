# Pulso · Aptitudes y oportunidades

Proyecto académico en React para registrar una empresa y sus vacantes, aplicar una autoevaluación de aptitudes y generar una comparación explicable de los puestos disponibles.

## Ejecutar

Requiere Node.js 20.19+ o 22.12+ y npm.

```bash
npm ci
npm run dev
```

Abre la dirección que muestra Vite (normalmente http://127.0.0.1:5173).

```bash
npm test
npm run build
npm run preview
```

## Recorrido

1. Escribe el nombre de la empresa y, opcionalmente, su sector.
2. Agrega vacantes usando las plantillas o personalizando nombre, responsabilidades y seis prioridades de 0 a 5.
3. Selecciona «Evaluar candidato», escribe un nombre o alias y acepta el procesamiento local.
4. Responde las 12 preguntas de autoevaluación.
5. Consulta fortalezas, áreas de mejora, ranking de vacantes y desglose de cada cálculo.
6. Descarga el reporte JSON o utiliza Imprimir / PDF. Puedes evaluar otra persona y consultar evaluaciones anteriores de la sesión.
7. En «Consulta en español», escribe una pregunta (por ejemplo «¿Qué es la salud mental?»), selecciona un tema y consulta respuestas del dataset con su original. También puedes abrir la consulta desde la encuesta y regresar sin perder respuestas.

La aplicación guarda datos solo en memoria: recargar elimina empresa, vacantes y evaluaciones. También existe «Borrar datos de la sesión». Los archivos descargados permanecen en el dispositivo. No hay autenticación, API ni base de datos; este prototipo no es un sistema multiusuario. Las fuentes tipográficas se solicitan a Google Fonts con alternativas locales; las respuestas no se envían a ese servicio.

## Dataset y método

`KB_limpio.json` se integra directamente en la aplicación y contiene 79 intenciones conversacionales de bienestar, principalmente en inglés. Se usa para recuperar preguntas y respuestas en una consulta interactiva bilingüe, separada de la puntuación laboral. La traducción parcial cubre las 79 intenciones: 128 frases traducidas y 79 respuestas traducidas o resumidas. El original se conserva íntegro y cada traducción referencia su posición en él. No contiene etiquetas de aptitudes o puestos y no se usa para inferir idoneidad a partir de salud mental.

La recomendación emplea reglas: seis aptitudes, dos preguntas por aptitud y promedio ponderado según las prioridades de cada vacante. No se ha entrenado un modelo predictivo. Las preguntas, pesos y umbrales son propuestas académicas sin validación psicométrica. El resultado debe complementarse con entrevista y pruebas laborales.

Consulta la [documentación](documentacion/README.md) para conocer requisitos, arquitectura, fórmulas, dataset y pruebas.
