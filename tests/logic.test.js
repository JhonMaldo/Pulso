import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { armarRespuestas, compararRequisitos, etiquetaFuente, mensajeError, nivel, progreso, respondidas, tipoRequisito } from '../src/logic.js';

const datos = JSON.parse(readFileSync(new URL('../backend/datos/preguntas.json', import.meta.url)));
const vacantes = JSON.parse(readFileSync(new URL('../backend/datos/vacantes.json', import.meta.url))).vacantes;
const nombres = Object.fromEntries(datos.aptitudes.map(a => [a.id, a.nombre]));

test('la prueba tiene las 8 aptitudes del plan y de 16 a 24 preguntas', () => {
 assert.deepEqual(datos.aptitudes.map(a => a.id), ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8']);
 assert.ok(datos.preguntas.length >= 16 && datos.preguntas.length <= 24);
 for (const a of datos.aptitudes) assert.ok(datos.preguntas.filter(p => p.aptitud === a.id).length >= 2);
});

test('arma el cuerpo de /api/evaluar con llaves de texto y exige todas las respuestas', () => {
 const answers = Object.fromEntries(datos.preguntas.map(p => [p.id, p.tipo === 'escala' ? 3 : 0]));
 const cuerpo = armarRespuestas(datos.preguntas, answers);
 assert.equal(Object.keys(cuerpo.respuestas).length, datos.preguntas.length);
 assert.equal(cuerpo.respuestas['1'], 0);
 delete answers[5];
 assert.throws(() => armarRespuestas(datos.preguntas, answers), /pregunta 5/);
});

test('el progreso cuenta solo respuestas válidas', () => {
 const p = datos.preguntas.slice(0, 4);
 assert.equal(progreso(p, {}), 0);
 assert.equal(respondidas(p, { 1: 0, 2: null, 3: 2 }), 2);
 assert.equal(progreso(p, { 1: 0, 2: 1, 3: 2, 4: 3 }), 100);
 assert.equal(progreso([], {}), 0);
});

test('compara requisitos contra el perfil con las claves primero', () => {
 const v01 = vacantes.find(v => v.id === 'V01');
 const filas = compararRequisitos(v01, { A1: 75, A6: 45, A3: 80 }, nombres);
 assert.deepEqual(filas.map(f => f.aptitud), ['A1', 'A6', 'A7', 'A3']);
 assert.equal(filas.find(f => f.aptitud === 'A6').cumple, false);
 assert.equal(filas.find(f => f.aptitud === 'A7').perfil, 0);
 assert.equal(filas[0].nombre, 'Razonamiento lógico');
 assert.equal(tipoRequisito(3), 'Clave');
 assert.equal(tipoRequisito(1), 'De apoyo');
});

test('etiquetas de nivel y de fuente de la explicación', () => {
 assert.equal(nivel(75), 'Fortaleza');
 assert.equal(nivel(50), 'En desarrollo');
 assert.equal(nivel(49), 'Por mejorar');
 assert.equal(etiquetaFuente('ia'), 'Generada con IA');
 assert.equal(etiquetaFuente('plantilla'), 'Explicación automática');
});

test('mensajes de error claros sin conexión, con límite y con detalle de la API', () => {
 assert.match(mensajeError(0), /conexión/);
 assert.match(mensajeError(429), /muchas solicitudes/);
 assert.match(mensajeError(502), /servidor/);
 assert.equal(mensajeError(422, { detail: 'Faltan respuestas' }), 'Faltan respuestas');
 assert.equal(mensajeError(422, { detail: [{ msg: 'x' }] }), 'No se pudo completar la solicitud.');
});

test('ayudantes de reportes', async () => {
 const { etiquetaDia, porcentaje, vacantesRecomendadas, rangoValido } = await import('../src/logic.js');
 assert.equal(etiquetaDia('2026-10-22'), '22 oct');
 assert.equal(etiquetaDia('2026-01-05'), '5 ene');
 assert.equal(porcentaje(3, 4), 75);
 assert.equal(porcentaje(1, 0), 0);
 const v = [{ id: 'V01', veces_top5: 3 }, { id: 'V02', veces_top5: 1 }, { id: 'V03', veces_top5: 0 }];
 assert.deepEqual(vacantesRecomendadas(v).map(x => x.id), ['V01', 'V02']);
 assert.deepEqual(vacantesRecomendadas(v, 1).map(x => x.id), ['V01']);
 assert.equal(rangoValido('2026-10-01', '2026-10-30'), '');
 assert.match(rangoValido('2026-10-30', '2026-10-01'), /posterior/);
});
