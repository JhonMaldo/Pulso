# Manual y validación

## Instalación

Con Node.js 20.19+ o 22.12+ y npm, ejecutar `npm ci` y `npm run dev` desde la raíz. Para una compilación estática, usar `npm run build`; `npm run preview` permite servir `dist/` localmente. No se necesitan variables de entorno ni claves de API.

## Prueba manual del proceso

1. Abrir Empresa y vacantes. Sin nombre de empresa y sin vacantes, Evaluar candidato debe estar deshabilitado.
2. Agregar una empresa y dos vacantes con prioridades diferentes. Intentar repetir un nombre y agregar un perfil con todas las prioridades en cero: se debe informar el error.
3. Iniciar la evaluación, escribir un alias y aceptar el procesamiento local.
4. Responder las 12 preguntas, retroceder y comprobar que se conservan las respuestas. La finalización debe estar deshabilitada si falta consentimiento, alias o respuesta.
5. Consultar perfil, fortalezas, áreas de mejora, ranking y detalles. Todas las respuestas en 5 deben producir 100; todas en 1 deben producir 0. Ambos casos generan empate entre vacantes y deben anunciarlo.
6. Descargar JSON y comprobar que contiene la empresa, alias, respuestas y vacantes evaluadas. Utilizar Imprimir / PDF y revisar la vista previa del navegador.
7. Evaluar otra persona y volver al reporte anterior con el selector del historial. Cambiar vacantes no debe modificar reportes ya terminados.
8. Abrir «Consulta en español» y probar «¿Qué es la salud mental?», «Estoy bajo mucha presión», «No puedo dormir» y «Me siento triste». Revisar la respuesta, su etiqueta de traducción/resumen, y el original. Buscar `work` también debe recuperar coincidencias en inglés. Una cadena inexistente debe mostrar el estado vacío; palabras genéricas como «¿qué?» no deben adivinar un tema. Seleccionar cualquier tema del catálogo debe funcionar sin consulta. Desde la encuesta, abrir la consulta y volver: alias, consentimiento y respuestas deben conservarse.
9. Borrar datos de la sesión y confirmar que desaparecen empresa, vacantes y evaluaciones. Recargar debe tener el mismo efecto sobre los datos. Los archivos descargados no se borran.
10. Revisar navegación por teclado, foco visible y diseño en anchos de móvil y escritorio.

## Pruebas automáticas

`npm test` ejecuta pruebas de Node sobre el modelo: cobertura de las seis dimensiones, extremos de escala, promedio entre preguntas, pesos cero, ponderación asimétrica, entradas inválidas, empates, ausencia de mutaciones y recuperación de ejemplos del dataset real.

`npm run build` comprueba que Vite puede transformar React, importar el dataset y generar los recursos estáticos. Estos controles no sustituyen una prueba interactiva de navegador ni una validación psicométrica. La lista manual anterior es una guía de aceptación, no una afirmación de que se haya automatizado o ejecutado en un navegador.

`tests/knowledge.test.js` agrega cinco pruebas para cobertura de las 79 intenciones y 128 traducciones, referencias reales al dataset, búsquedas bilingües, consultas sin coincidencia, ausencia de copias del original en la capa española y detección de índices inválidos. Se conservan las seis pruebas de evaluación anteriores.
