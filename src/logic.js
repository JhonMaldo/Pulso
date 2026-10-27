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

// ---------- Panel del jefe ----------
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
export const etiquetaDia = iso => `${Number(iso.slice(8, 10))} ${MESES[Number(iso.slice(5, 7)) - 1]}`;
export const porcentaje = (parte, total) => total ? Math.round(parte / total * 100) : 0;
export function rangoValido(desde, hasta) {
 if (desde && hasta && desde > hasta) return 'La fecha «desde» no puede ser posterior a «hasta».';
 return '';
}

// Niveles de preparación, en el orden en que se muestran. Los textos los ve el jefe.
export const NIVELES = [
 { id: 'preparado', nombre: 'Preparado', detalle: 'Cumple todos los mínimos del puesto que mejor le queda' },
 { id: 'reforzar', nombre: 'Le faltan habilidades', detalle: 'Tiene brechas, pero afinidad de 75 % o más' },
 { id: 'no_apto', nombre: 'No apto por ahora', detalle: 'Afinidad menor a 75 %: debería reforzarse o buscar otra área' },
];

// Porcentajes que siempre suman 100 (método del mayor residuo), para la barra y las tarjetas.
export function porcentajesNiveles(niveles) {
 const total = NIVELES.reduce((s, n) => s + (niveles[n.id] || 0), 0);
 if (!total) return Object.fromEntries(NIVELES.map(n => [n.id, 0]));
 const exactos = NIVELES.map(n => ({ id: n.id, v: (niveles[n.id] || 0) / total * 100 }));
 const base = exactos.map(e => ({ ...e, p: Math.floor(e.v) }));
 let faltan = 100 - base.reduce((s, e) => s + e.p, 0);
 [...base].sort((a, b) => (b.v - b.p) - (a.v - a.p)).forEach(e => { if (faltan > 0 && e.v > e.p) { e.p += 1; faltan -= 1; } });
 return Object.fromEntries(base.map(e => [e.id, e.p]));
}

// Mensaje para la persona evaluada, según su nivel en el puesto que mejor le queda.
export const MENSAJE_NIVEL = {
 preparado: 'Cumples todos los requisitos de este puesto.',
 reforzar: 'Te faltan algunas habilidades para este puesto: revisa tus brechas.',
 no_apto: 'Todavía no alcanzas lo que piden estos puestos. Refuerza tus aptitudes más bajas o explora otras áreas.',
};

// Cuerpo de POST /api/jefe/puestos a partir del formulario.
export function armarPuesto(f) {
 const habilidades = f.habilidades.split(',').map(h => h.trim()).filter(Boolean);
 const requisitos = Object.fromEntries(Object.entries(f.requisitos).filter(([, v]) => v));
 if (!Object.keys(requisitos).length) throw new Error('Elige al menos una aptitud que pida el puesto.');
 if (habilidades.length > 8) throw new Error('Escribe como máximo 8 habilidades clave.');
 return { titulo: f.titulo.trim(), empresa: f.empresa.trim(), area: f.area.trim(), modalidad: f.modalidad,
  descripcion: f.descripcion.trim(), habilidades_clave: habilidades, requisitos };
}
