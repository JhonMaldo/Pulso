# Idea de negocio: Pulso

**Nombre:** Pulso · Aptitudes y vacantes

**Lema:** De tu potencial a tu primera oportunidad.

## Problema

En México, miles de jóvenes egresan cada semestre sin saber para qué puestos tienen mejores aptitudes. Las bolsas de trabajo filtran por palabras clave y experiencia, así que quien busca su primer empleo manda decenas de solicitudes a ciegas, recibe rechazos sin explicación y no sabe qué mejorar. Para las empresas pequeñas, filtrar candidatos junior es lento y no tienen herramientas de evaluación.

## Usuario final

- **Principal:** estudiantes de últimos semestres y recién egresados de universidades y tecnológicos que buscan su primer empleo o quieren cambiar de área.
- **Secundario:** bolsas de trabajo universitarias y pymes que publican vacantes junior.

## Solución

Una aplicación web, usable desde el celular, que:

1. Aplica una prueba corta (unos 10 minutos) de 8 aptitudes: razonamiento lógico y numérico, comunicación, trabajo en equipo, organización, resolución de problemas, atención al detalle y servicio al cliente.
2. Calcula un perfil de 0 a 100 y la afinidad con cada vacante con una fórmula transparente.
3. Recomienda las 5 vacantes más afines con fortalezas y brechas concretas («te faltan 15 puntos de atención al detalle»).
4. Explica cada recomendación con un modelo de IA local (Ollama) que consulta al motor mediante herramientas, sin inventar números.
5. Acompaña a la persona durante la búsqueda con un módulo de apoyo emocional basado en un dataset abierto, que nunca influye en sus resultados.

## Valor agregado

- **Explicable:** cada porcentaje se puede justificar; la IA redacta, pero no decide ni calcula.
- **Privado por diseño:** no pide datos personales ni guarda respuestas; la IA corre en infraestructura propia (no se envían datos a terceros).
- **Orientado a mejorar:** no solo dice «sí o no», dice qué aptitud trabajar para cada puesto.
- **Barato de operar:** un servidor ligero con NGINX y una computadora local con Ollama, unidos por VPN.

## Cómo se cobraría

| Cliente | Modelo | Precio estimado |
|---|---|---|
| Candidato | Gratis (prueba, perfil y 5 recomendaciones) | $0 |
| Bolsas de trabajo universitarias | Licencia anual con su propio catálogo de vacantes y reportes agregados y anónimos de aptitudes de sus egresados | $25,000 MXN al año por institución |
| Pymes | Publicar vacantes con requisitos de aptitudes y ver cuántos perfiles afines hay (nunca datos individuales sin consentimiento) | $499 MXN al mes |

**Siguientes pasos:** validar las preguntas con un especialista en psicometría, piloto con la bolsa de trabajo del instituto y catálogo con vacantes reales.

*Las vacantes actuales son datos de ejemplo. La prueba es una orientación y no decide contrataciones.*
