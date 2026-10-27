import React, { useState } from 'react';
import { explicar } from './api.js';
import { MENSAJE_NIVEL, NIVELES, compararRequisitos, etiquetaFuente, nivel, tipoRequisito } from './logic.js';

export function Perfil({ perfil, aptitudes }) {
 return <div className="card">
  <h3>Tu perfil de aptitudes</h3>
  <p className="subtle">Puntaje de 0 a 100 por aptitud. 75 o más: fortaleza · 50 a 74: en desarrollo · menos de 50: por mejorar.</p>
  <ul className="bars" aria-label="Gráfica de las 8 aptitudes">
   {aptitudes.map(a => <li className="skill-score" key={a.id}>
    <div className="row"><span>{a.nombre}</span><b>{perfil[a.id] ?? 0} <small>· {nivel(perfil[a.id] ?? 0)}</small></b></div>
    <div className="progress" aria-hidden="true"><span style={{ width: `${perfil[a.id] ?? 0}%` }}/></div>
   </li>)}
  </ul>
 </div>;
}

export function Resultados({ resultado, aptitudes, alias, onDetalle, onReiniciar }) {
 const [primera] = resultado.recomendaciones;
 return <>
  <div className="section-title"><p className="eyebrow">RESULTADOS</p><h3>{alias ? `${alias}, este` : 'Este'} es tu punto de partida.</h3><p>Las vacantes son datos de ejemplo. La afinidad es una orientación, no una probabilidad de contratación.</p></div>
  <div className="result-banner"><div><span className="eyebrow">MAYOR AFINIDAD</span><h2>{primera.vacante.titulo}</h2><p>{primera.vacante.area} · {primera.vacante.modalidad}</p></div><strong>{primera.afinidad}<small>%</small></strong></div>
  {resultado.nivel && <p className={`nivel-mensaje nivel-borde-${resultado.nivel}`}><b>{NIVELES.find(n => n.id === resultado.nivel)?.nombre}.</b> {MENSAJE_NIVEL[resultado.nivel]}</p>}
  <div className="result-grid">
   <Perfil perfil={resultado.perfil} aptitudes={aptitudes}/>
   <div className="card">
    <h3>Las 5 vacantes que mejor encajan</h3>
    <ol className="vacantes">
     {resultado.recomendaciones.map((r, i) => <li key={r.vacante.id}>
      <button className="vacante" onClick={() => onDetalle(r)}>
       <span className="pos">{String(i + 1).padStart(2, '0')}</span>
       <span className="info"><b>{r.vacante.titulo}</b><small>{r.vacante.area} · {r.brechas.length ? `${r.brechas.length} brecha${r.brechas.length > 1 ? 's' : ''}` : 'Sin brechas'}</small></span>
       <strong>{r.afinidad}%</strong>
      </button>
      <div className="meter" aria-hidden="true"><span style={{ width: `${r.afinidad}%` }}/></div>
     </li>)}
    </ol>
    <p className="subtle">Toca una vacante para ver sus requisitos y el botón «¿Por qué?».</p>
   </div>
  </div>
  <div className="bottom-action"><p>Tus respuestas no se guardan. Al recargar la página se borran.</p><button className="button secondary" onClick={onReiniciar}>Volver a empezar</button></div>
 </>;
}

export function Detalle({ rec, perfil, aptitudes, explicacion, onExplicacion, onVolver }) {
 const [cargando, setCargando] = useState(false);
 const [error, setError] = useState('');
 const nombres = Object.fromEntries(aptitudes.map(a => [a.id, a.nombre]));
 const filas = compararRequisitos(rec.vacante, perfil, nombres);
 const v = rec.vacante;
 async function porQue() {
  setCargando(true); setError('');
  try { onExplicacion(v.id, await explicar(v.id, perfil)); }
  catch (e) { setError(e.message); }
  finally { setCargando(false); }
 }
 return <>
  <button className="button secondary back" onClick={onVolver}>← Volver a resultados</button>
  <div className="result-banner"><div><span className="eyebrow">{v.area.toUpperCase()} · {v.modalidad.toUpperCase()}</span><h2>{v.titulo}</h2><p>{v.descripcion}</p></div><strong>{rec.afinidad}<small>%</small></strong></div>
  <p className="subtle">Habilidades clave del puesto: {v.habilidades_clave.join(' · ')} · {v.empresa} (dato de ejemplo)</p>
  <div className="card">
   <h3>Requisitos contra tu perfil</h3>
   <div className="table-scroll"><table>
    <thead><tr><th>Aptitud</th><th>Tipo</th><th>Mín.</th><th>Tú</th><th>Estado</th></tr></thead>
    <tbody>{filas.map(f => <tr key={f.aptitud}><td>{f.nombre}</td><td title={`Peso ${f.peso}`}>{tipoRequisito(f.peso)}</td><td>{f.minimo}</td><td>{f.perfil}</td><td className={f.cumple ? 'ok' : 'gap'}>{f.cumple ? '✓ Cumple' : '△ Brecha'}</td></tr>)}</tbody>
   </table></div>
   <p className="subtle">Clave = peso 3 · De apoyo = peso 1 o 2. Afinidad = 100 × suma(peso × mín(perfil ÷ mínimo, 1)) ÷ suma(pesos).</p>
  </div>
  <div className="result-grid">
   <div className="card"><h3>↗ Fortalezas para este puesto</h3><p>{rec.fortalezas.map(f => f.nombre).join(' · ') || 'Todavía ninguna aptitud alcanza el mínimo.'}</p></div>
   <div className="card"><h3>△ Qué puedes mejorar</h3><p>{rec.brechas.map(b => `${b.nombre} (${b.perfil} de ${b.minimo})`).join(' · ') || 'Alcanzas todos los mínimos de esta vacante.'}</p></div>
  </div>
  <div className="card why">
   <div className="row"><h3>¿Por qué me recomiendan esta vacante?</h3>{!explicacion && <button className="button primary" onClick={porQue} disabled={cargando}>{cargando ? 'Cargando…' : '¿Por qué?'}</button>}</div>
   {cargando && <p role="status" className="notice">Cargando la explicación. La IA corre en una computadora del equipo y puede tardar hasta 2 minutos.</p>}
   {error && <p role="alert" className="error">{error} <button className="link" onClick={porQue}>Reintentar</button></p>}
   {explicacion && <div aria-live="polite">
    <span className={`source-badge ${explicacion.fuente}`}>{etiquetaFuente(explicacion.fuente)}</span>
    <p className="answer-text">{explicacion.texto}</p>
    {explicacion.fuente === 'ia' && explicacion.herramientas?.length > 0 && <p className="subtle">La IA consultó al motor con las herramientas: {explicacion.herramientas.join(', ')}. Los números salen del motor; la IA solo los explica.</p>}
    {explicacion.fuente === 'plantilla' && <p className="subtle">La IA no respondió a tiempo o su respuesta no coincidió con el motor, así que se muestra la explicación automática con los mismos datos.</p>}
   </div>}
  </div>
 </>;
}
