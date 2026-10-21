import { mensajeError } from './logic.js';

// Todas las rutas son relativas: en la VM las sirve FastAPI y desde Internet pasan por NGINX.
async function pedir(ruta, cuerpo) {
 let r;
 try {
  r = await fetch(ruta, cuerpo === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) });
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
