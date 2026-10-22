// Lógica de las pantallas sin React, para poder probarla con node --test.
// El perfil y las recomendaciones los calcula la API; aquí solo se arma y se muestra.

export const normalize = s => s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim();

// answers: {id_de_pregunta: valor}. Devuelve el cuerpo de POST /api/evaluar.
export function armarRespuestas(preguntas, answers) {
 const respuestas = {};
 for (const p of preguntas) {
  if (!Number.isInteger(answers[p.id])) throw new Error(`Falta responder la pregunta ${p.id}.`);
  respuestas[String(p.id)] = answers[p.id];
 }
 return { respuestas };
}

export const respondidas = (preguntas, answers) => preguntas.filter(p => Number.isInteger(answers[p.id])).length;
export const progreso = (preguntas, answers) => preguntas.length ? Math.round(respondidas(preguntas, answers) / preguntas.length * 100) : 0;

export function nivel(puntaje) {
 if (puntaje >= 75) return 'Fortaleza';
 if (puntaje >= 50) return 'En desarrollo';
 return 'Por mejorar';
}

export const etiquetaFuente = fuente => fuente === 'ia' ? 'Generada con IA' : 'Explicación automática';
export const tipoRequisito = peso => peso >= 3 ? 'Clave' : 'De apoyo';

// Requisitos de una vacante contra el perfil, en el orden de importancia.
export function compararRequisitos(vacante, perfil, nombres) {
 return Object.entries(vacante.requisitos)
  .map(([aptitud, r]) => ({ aptitud, nombre: nombres[aptitud] || aptitud, perfil: perfil[aptitud] ?? 0, minimo: r.minimo, peso: r.peso, cumple: (perfil[aptitud] ?? 0) >= r.minimo }))
  .sort((a, b) => b.peso - a.peso || a.aptitud.localeCompare(b.aptitud));
}

// Mensaje claro para errores de red o de la API.
export function mensajeError(status, cuerpo) {
 if (!status) return 'No hay conexión con el servidor. Revisa tu internet e inténtalo de nuevo.';
 if (status === 429) return 'Hay muchas solicitudes en este momento. Espera unos segundos e inténtalo de nuevo.';
 if (status >= 500) return 'El servidor tuvo un problema. Inténtalo de nuevo en un momento.';
 const d = cuerpo?.detail;
 return typeof d === 'string' ? d : 'No se pudo completar la solicitud.';
}

// ---------- Reportes ----------
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
export const etiquetaDia = iso => `${Number(iso.slice(8, 10))} ${MESES[Number(iso.slice(5, 7)) - 1]}`;
export const porcentaje = (parte, total) => total ? Math.round(parte / total * 100) : 0;
// Solo las vacantes que sí aparecieron en algún top 5, de más a menos recomendada.
export const vacantesRecomendadas = (vacantes, n = 10) => vacantes.filter(v => v.veces_top5 > 0).slice(0, n);
export function rangoValido(desde, hasta) {
 if (desde && hasta && desde > hasta) return 'La fecha «desde» no puede ser posterior a «hasta».';
 return '';
}
