import { mensajeError } from './logic.js';

// Todas las rutas son relativas: en la VM las sirve FastAPI y desde Internet pasan por NGINX.
async function pedir(ruta, cuerpo, encabezados = {}) {
 let r;
 try {
  r = await fetch(ruta, cuerpo === undefined ? { headers: encabezados } : { method: 'POST', headers: { 'Content-Type': 'application/json', ...encabezados }, body: JSON.stringify(cuerpo) });
 } catch {
  throw new Error(mensajeError(0));
 }
 const datos = await r.json().catch(() => null);
 if (!r.ok) throw new Error(mensajeError(r.status, datos));
 if (!datos) throw new Error('La respuesta del servidor llegó incompleta.');
 return datos;
}

export const obtenerPrueba = () => pedir('/api/prueba');
export const evaluar = cuerpo => pedir('/api/evaluar', cuerpo);
export const explicar = (vacante_id, perfil) => pedir('/api/explicar', { vacante_id, perfil });
export const pedirApoyo = texto => pedir('/api/apoyo', { texto });

// Panel del jefe: todas las llamadas llevan la contraseña en el encabezado X-Clave-Jefe.
const jefe = clave => ({ 'X-Clave-Jefe': clave });
const rango = (desde, hasta) => new URLSearchParams(Object.entries({ desde, hasta }).filter(([, v]) => v)).toString();
export const entrarJefe = clave => pedir('/api/jefe/acceso', undefined, jefe(clave));
export const obtenerEstadisticas = (clave, desde, hasta) => pedir(`/api/jefe/estadisticas?${rango(desde, hasta)}`, undefined, jefe(clave));
export const obtenerPuestos = clave => pedir('/api/jefe/puestos', undefined, jefe(clave));
export const crearPuesto = (clave, puesto) => pedir('/api/jefe/puestos', puesto, jefe(clave));
export async function cambiarEstadoPuesto(clave, id, activa) {
 let r;
 try { r = await fetch(`/api/jefe/puestos/${encodeURIComponent(id)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', ...jefe(clave) }, body: JSON.stringify({ activa }) }); }
 catch { throw new Error(mensajeError(0)); }
 const datos = await r.json().catch(() => null);
 if (!r.ok) throw new Error(mensajeError(r.status, datos));
 return datos;
}
export async function descargarCsv(clave, desde, hasta) {
 let r;
 try { r = await fetch(`/api/jefe/resultados.csv?${rango(desde, hasta)}`, { headers: jefe(clave) }); }
 catch { throw new Error(mensajeError(0)); }
 if (!r.ok) throw new Error(mensajeError(r.status, await r.json().catch(() => null)));
 const url = URL.createObjectURL(await r.blob()), a = document.createElement('a');
 a.href = url; a.download = 'pulso_resultados.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
