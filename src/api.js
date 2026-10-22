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

// Reportes (datos anónimos y agregados). La clave solo se pide si el servidor tiene REPORTES_CLAVE.
const conClave = clave => clave ? { 'X-Clave-Reportes': clave } : {};
const rango = (desde, hasta) => new URLSearchParams(Object.entries({ desde, hasta }).filter(([, v]) => v)).toString();
export const accesoReportes = () => pedir('/api/reportes/acceso');
export const obtenerReportes = (desde, hasta, clave) => pedir(`/api/reportes/resumen?${rango(desde, hasta)}`, undefined, conClave(clave));
export async function descargarCsv(desde, hasta, clave) {
 let r;
 try { r = await fetch(`/api/reportes/evaluaciones.csv?${rango(desde, hasta)}`, { headers: conClave(clave) }); }
 catch { throw new Error(mensajeError(0)); }
 if (!r.ok) throw new Error(mensajeError(r.status, await r.json().catch(() => null)));
 const url = URL.createObjectURL(await r.blob()), a = document.createElement('a');
 a.href = url; a.download = 'pulso_evaluaciones.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
