import React, { useEffect, useState } from 'react';
import { accesoReportes, descargarCsv, obtenerReportes } from './api.js';
import { etiquetaDia, porcentaje, rangoValido, vacantesRecomendadas } from './logic.js';

// Reportes para reclutadores y administradores: solo datos anónimos y agregados de la base de datos.
export default function Reportes() {
 const [desde, setDesde] = useState('');
 const [hasta, setHasta] = useState('');
 const [clave, setClave] = useState('');
 const [pideClave, setPideClave] = useState(false);
 const [datos, setDatos] = useState(null);
 const [cargando, setCargando] = useState(false);
 const [error, setError] = useState('');

 async function cargar(c = clave) {
  const problema = rangoValido(desde, hasta);
  if (problema) return setError(problema);
  setCargando(true); setError('');
  try { setDatos(await obtenerReportes(desde, hasta, c)); }
  catch (e) { setError(e.message); setDatos(null); }
  finally { setCargando(false); }
 }
 async function csv() {
  setError('');
  try { await descargarCsv(desde, hasta, clave); } catch (e) { setError(e.message); }
 }
 useEffect(() => {
  accesoReportes().then(a => { setPideClave(a.requiere_clave); if (!a.requiere_clave) cargar(''); }).catch(e => setError(e.message));
 }, []);

 const ia = datos?.explicaciones;
 const top = datos ? vacantesRecomendadas(datos.vacantes) : [];
 const maxDia = datos ? Math.max(1, ...datos.por_dia.map(d => d.evaluaciones)) : 1;

 return <section aria-labelledby="reportes-titulo">
  <div className="section-title"><p className="eyebrow">REPORTES · BASE DE DATOS SQLite</p><h3 id="reportes-titulo">Así se está usando Pulso.</h3><p>Datos anónimos y agregados. No se guardan nombres, respuestas individuales ni lo que se escribe en «Apoyo».</p></div>

  <form className="filtros" onSubmit={e => { e.preventDefault(); cargar(); }}>
   <label>Desde<input type="date" value={desde} onChange={e => setDesde(e.target.value)}/></label>
   <label>Hasta<input type="date" value={hasta} onChange={e => setHasta(e.target.value)}/></label>
   {pideClave && <label>Clave de reportes<input type="password" autoComplete="off" value={clave} onChange={e => setClave(e.target.value)} required/></label>}
   <div className="filtros-botones">
    <button className="button primary" disabled={cargando}>{cargando ? 'Cargando…' : 'Ver reporte'}</button>
    <button type="button" className="button secondary" onClick={csv} disabled={!datos}>↓ Descargar CSV</button>
   </div>
  </form>
  {error && <p role="alert" className="error">{error}</p>}

  {datos && datos.evaluaciones === 0 && <p className="notice">Todavía no hay evaluaciones registradas en este periodo.</p>}

  {datos && datos.evaluaciones > 0 && <>
   <div className="kpis">
    <div className="card kpi"><span>Evaluaciones</span><strong>{datos.evaluaciones}</strong><small>{datos.desde || datos.hasta ? 'en el periodo elegido' : 'desde que se publicó'}</small></div>
    <div className="card kpi"><span>Explicaciones con IA</span><strong>{porcentaje(ia.con_ia, ia.total)}%</strong><small>{ia.con_ia} de {ia.total} «¿Por qué?»</small></div>
    <div className="card kpi"><span>Tiempo promedio de la IA</span><strong>{ia.segundos_ia == null ? '—' : <>{ia.segundos_ia}<em> s</em></>}</strong><small>sin contar respuestas en memoria</small></div>
    <div className="card kpi"><span>Vacante más recomendada</span><strong className="kpi-texto">{top[0]?.titulo ?? '—'}</strong><small>{top[0] ? `${top[0].veces_top5} veces en el top 5` : ''}</small></div>
   </div>

   <div className="result-grid">
    <div className="card">
     <h3>Promedio por aptitud</h3>
     <p className="subtle">Puntaje promedio de 0 a 100 de todas las evaluaciones del periodo.</p>
     <ul className="bars" aria-label="Promedio por aptitud">
      {datos.aptitudes.map(a => <li className="skill-score" key={a.id} title={`${a.nombre}: ${a.promedio ?? 0} de 100 (${a.n} evaluaciones)`}>
       <div className="row"><span>{a.nombre}</span><b>{a.promedio ?? '—'}</b></div>
       <div className="progress" aria-hidden="true"><span style={{ width: `${a.promedio ?? 0}%` }}/></div>
      </li>)}
     </ul>
    </div>
    <div className="card">
     <h3>Evaluaciones por día</h3>
     <p className="subtle">Hora de México.</p>
     <div className="columnas" role="img" aria-label={datos.por_dia.map(d => `${etiquetaDia(d.fecha)}: ${d.evaluaciones}`).join(', ')}>
      {datos.por_dia.map(d => <div className="columna" key={d.fecha} title={`${d.fecha}: ${d.evaluaciones} evaluaciones`}>
       <b>{d.evaluaciones}</b>
       <div className="columna-barra"><span style={{ height: `${d.evaluaciones / maxDia * 100}%` }}/></div>
       <small>{etiquetaDia(d.fecha)}</small>
      </div>)}
     </div>
    </div>
   </div>

   <div className="card">
    <h3>Vacantes más recomendadas</h3>
    <div className="table-scroll"><table>
     <thead><tr><th>Vacante</th><th className="col-area">Área</th><th>En el top 5</th><th>En 1er lugar</th><th>Afinidad promedio</th></tr></thead>
     <tbody>{top.map(v => <tr key={v.id}><td>{v.titulo}</td><td className="col-area">{v.area}</td><td>{v.veces_top5}</td><td>{v.veces_primera}</td><td>{v.afinidad_promedio}%</td></tr>)}</tbody>
    </table></div>
    <p className="subtle">Las vacantes son datos de ejemplo. El CSV trae una fila por evaluación anónima: fecha, puntaje por aptitud y la vacante con mayor afinidad.</p>
   </div>
  </>}
 </section>;
}
