import React, { useEffect, useState } from 'react';
import { cambiarEstadoPuesto, crearPuesto, descargarCsv, entrarJefe, obtenerEstadisticas, obtenerPuestos } from './api.js';
import { NIVELES, armarPuesto, etiquetaDia, porcentajesNiveles, rangoValido } from './logic.js';

const FORMULARIO = { titulo: '', empresa: '', area: '', modalidad: 'Presencial', descripcion: '', habilidades: '', requisitos: {} };
const IMPORTANCIAS = [['', 'No aplica'], ['deseable', 'Deseable (mín. 40)'], ['importante', 'Importante (mín. 50)'], ['clave', 'Clave (mín. 60)']];

// Barra de 100 % con los 3 niveles. Cada segmento lleva su etiqueta: el color nunca es la única pista.
function BarraNiveles({ niveles, alto = 34, etiquetas = true }) {
 const pct = porcentajesNiveles(niveles);
 return <div className="barra-niveles" style={{ height: alto }} role="img"
  aria-label={NIVELES.map(n => `${n.nombre}: ${pct[n.id]} %`).join(', ')}>
  {NIVELES.filter(n => pct[n.id] > 0).map(n =>
   <span key={n.id} className={`seg nivel-${n.id}`} style={{ flexGrow: pct[n.id] }} title={`${n.nombre}: ${niveles[n.id]} (${pct[n.id]} %)`}>
    {etiquetas && pct[n.id] >= 12 && `${pct[n.id]} %`}
   </span>)}
 </div>;
}

function Estadisticas({ clave }) {
 const [desde, setDesde] = useState('');
 const [hasta, setHasta] = useState('');
 const [datos, setDatos] = useState(null);
 const [cargando, setCargando] = useState(false);
 const [error, setError] = useState('');
 async function cargar() {
  const problema = rangoValido(desde, hasta);
  if (problema) return setError(problema);
  setCargando(true); setError('');
  try { setDatos(await obtenerEstadisticas(clave, desde, hasta)); } catch (e) { setError(e.message); }
  finally { setCargando(false); }
 }
 useEffect(() => { cargar(); }, []);
 const pct = datos ? porcentajesNiveles(datos.niveles) : null;
 const maxDia = datos ? Math.max(1, ...datos.por_dia.map(d => d.evaluaciones)) : 1;

 return <>
  <form className="filtros" onSubmit={e => { e.preventDefault(); cargar(); }}>
   <label>Desde<input type="date" value={desde} onChange={e => setDesde(e.target.value)}/></label>
   <label>Hasta<input type="date" value={hasta} onChange={e => setHasta(e.target.value)}/></label>
   <div className="filtros-botones">
    <button className="button primary" disabled={cargando}>{cargando ? 'Cargando…' : 'Actualizar'}</button>
    <button type="button" className="button secondary" disabled={!datos?.evaluaciones} onClick={() => descargarCsv(clave, desde, hasta).catch(e => setError(e.message))}>↓ Descargar CSV</button>
   </div>
  </form>
  {error && <p role="alert" className="error">{error}</p>}
  {datos && datos.evaluaciones === 0 && <p className="notice">Todavía no hay evaluaciones en este periodo.</p>}
  {datos && datos.evaluaciones > 0 && <>
   <div className="card">
    <h3>¿Qué tan preparadas están las personas evaluadas?</h3>
    <p className="subtle">{datos.evaluaciones} evaluaciones{datos.desde || datos.hasta ? ' en el periodo elegido' : ''}. Cada persona cuenta una vez, según el puesto que mejor le queda.</p>
    <BarraNiveles niveles={datos.niveles}/>
    <div className="kpis kpis-3">
     {NIVELES.map(n => <div className={`kpi-nivel nivel-borde-${n.id}`} key={n.id}>
      <span className="kpi-nombre"><i className={`punto nivel-${n.id}`} aria-hidden="true"/>{n.nombre}</span>
      <strong>{pct[n.id]} %</strong>
      <small>{datos.niveles[n.id]} {datos.niveles[n.id] === 1 ? 'persona' : 'personas'} · {n.detalle}</small>
     </div>)}
    </div>
   </div>

   <div className="card">
    <h3>Por puesto</h3>
    <p className="subtle">Personas cuyo mejor resultado fue cada puesto.</p>
    <div className="table-scroll"><table>
     <thead><tr><th>Puesto</th><th>Personas</th><th>Afinidad prom.</th><th className="col-area">Preparado</th><th className="col-area">Le faltan</th><th className="col-area">No apto</th><th>Distribución</th></tr></thead>
     <tbody>{datos.por_puesto.map(p => <tr key={p.id}>
      <td>{p.titulo}{p.origen === 'jefe' && <small className="etiqueta-jefe">agregado por el jefe</small>}</td>
      <td>{p.personas}</td><td>{p.afinidad_promedio} %</td>
      <td className="col-area">{p.preparado}</td><td className="col-area">{p.reforzar}</td><td className="col-area">{p.no_apto}</td>
      <td className="celda-barra"><BarraNiveles niveles={p} alto={12} etiquetas={false}/></td>
     </tr>)}</tbody>
    </table></div>
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
  </>}
 </>;
}

function Puestos({ clave, aptitudes }) {
 const [puestos, setPuestos] = useState(null);
 const [f, setF] = useState(FORMULARIO);
 const [guardando, setGuardando] = useState(false);
 const [error, setError] = useState('');
 const [aviso, setAviso] = useState('');
 async function cargar() {
  try { setPuestos((await obtenerPuestos(clave)).puestos); } catch (e) { setError(e.message); }
 }
 useEffect(() => { cargar(); }, []);
 const campo = k => ({ value: f[k], onChange: e => setF({ ...f, [k]: e.target.value }) });
 async function guardar(e) {
  e.preventDefault(); setError(''); setAviso('');
  let cuerpo;
  try { cuerpo = armarPuesto(f); } catch (err) { return setError(err.message); }
  setGuardando(true);
  try {
   const p = await crearPuesto(clave, cuerpo);
   setAviso(`Se agregó «${p.titulo}» (${p.id}). Desde ahora se recomienda a quien haga la prueba.`);
   setF(FORMULARIO); cargar();
  } catch (err) { setError(err.message); }
  finally { setGuardando(false); }
 }
 async function alternar(p) {
  setError(''); setAviso('');
  try { await cambiarEstadoPuesto(clave, p.id, !p.activa); cargar(); } catch (e) { setError(e.message); }
 }
 const nombre = Object.fromEntries(aptitudes.map(a => [a.id, a.nombre]));
 const activos = puestos?.filter(p => p.activa).length ?? 0;

 return <>
  <form className="card" onSubmit={guardar}>
   <h3>Agregar un puesto</h3>
   <p className="subtle">El puesto queda disponible al instante: Pulso lo compara con el perfil de cada persona y lo recomienda si encaja.</p>
   <div className="form-grid">
    <label>Nombre del puesto<input required minLength={3} maxLength={80} {...campo('titulo')} placeholder="Ej. Recepcionista bilingüe"/></label>
    <label>Empresa<input required minLength={2} maxLength={80} {...campo('empresa')} placeholder="Ej. Hotel Las Palmas"/></label>
    <label>Área<input required minLength={2} maxLength={60} {...campo('area')} placeholder="Ej. Atención y ventas"/></label>
    <label>Modalidad<select {...campo('modalidad')}>{['Presencial', 'Híbrido', 'Remoto'].map(m => <option key={m}>{m}</option>)}</select></label>
   </div>
   <label>Descripción<textarea required minLength={10} maxLength={400} rows={2} {...campo('descripcion')} placeholder="¿Qué hará la persona?"/></label>
   <label>Habilidades clave (separadas por comas, máximo 8)<input maxLength={330} {...campo('habilidades')} placeholder="Ej. Inglés, Atención telefónica, Excel"/></label>
   <fieldset className="requisitos-form">
    <legend>¿Qué aptitudes pide el puesto?</legend>
    <p className="subtle">Clave = indispensable (peso 3) · Importante = peso 2 · Deseable = peso 1. Elige al menos una.</p>
    <div className="form-grid">
     {aptitudes.map(a => <label key={a.id}>{a.nombre}
      <select value={f.requisitos[a.id] || ''} onChange={e => setF({ ...f, requisitos: { ...f.requisitos, [a.id]: e.target.value } })}>
       {IMPORTANCIAS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
      </select></label>)}
    </div>
   </fieldset>
   {error && <p role="alert" className="error">{error}</p>}
   {aviso && <p role="status" className="notice">{aviso}</p>}
   <button className="button primary" disabled={guardando}>{guardando ? 'Guardando…' : '+ Agregar puesto'}</button>
  </form>

  <div className="card">
   <div className="row"><h3>Puestos</h3><span className="subtle">{activos} activos de {puestos?.length ?? 0}</span></div>
   <div className="table-scroll"><table>
    <thead><tr><th>Puesto</th><th className="col-area">Área</th><th>Pide</th><th>Estado</th><th></th></tr></thead>
    <tbody>{(puestos || []).map(p => <tr key={p.id} className={p.activa ? '' : 'inactivo'}>
     <td><b>{p.titulo}</b><small className="sub">{p.id} · {p.empresa}{p.origen === 'jefe' ? ` · agregado ${p.creada}` : ' · ejemplo'}</small></td>
     <td className="col-area">{p.area}</td>
     <td>{Object.entries(p.requisitos).filter(([, r]) => r.peso === 3).map(([a]) => nombre[a]).join(', ') || '—'}</td>
     <td>{p.activa ? 'Activo' : 'Inactivo'}</td>
     <td><button type="button" className="button secondary mini" onClick={() => alternar(p)}>{p.activa ? 'Desactivar' : 'Activar'}</button></td>
    </tr>)}</tbody>
   </table></div>
   <p className="subtle">«Pide» muestra las aptitudes clave. Desactivar un puesto deja de recomendarlo, pero conserva sus estadísticas.</p>
  </div>
 </>;
}

// Panel del jefe: estadísticas de preparación y alta de puestos. Protegido con la contraseña JEFE_CLAVE del servidor.
export default function Panel() {
 const [clave, setClave] = useState('');
 const [acceso, setAcceso] = useState(null);
 const [vista, setVista] = useState('estadisticas');
 const [error, setError] = useState('');
 const [entrando, setEntrando] = useState(false);
 async function entrar(e) {
  e.preventDefault(); setEntrando(true); setError('');
  try { setAcceso(await entrarJefe(clave)); } catch (err) { setError(err.message); }
  finally { setEntrando(false); }
 }
 if (!acceso) return <section aria-labelledby="panel-titulo" className="survey">
  <div className="section-title"><p className="eyebrow">PANEL DEL JEFE</p><h3 id="panel-titulo">Solo para quien administra los puestos.</h3><p>Aquí se ven las estadísticas de preparación y se agregan puestos nuevos.</p></div>
  <form onSubmit={entrar}>
   <label>Contraseña<input type="password" autoComplete="current-password" required value={clave} onChange={e => setClave(e.target.value)}/></label>
   {error && <p role="alert" className="error">{error}</p>}
   <button className="button primary" disabled={entrando}>{entrando ? 'Entrando…' : 'Entrar'}</button>
  </form>
 </section>;

 return <section aria-labelledby="panel-titulo">
  <div className="section-title row"><div><p className="eyebrow">PANEL DEL JEFE · BASE DE DATOS SQLite</p><h3 id="panel-titulo">{vista === 'estadisticas' ? 'Estadísticas de preparación' : 'Puestos disponibles'}</h3></div>
   <button type="button" className="button secondary mini" onClick={() => { setAcceso(null); setClave(''); }}>Salir</button></div>
  <div className="subtabs" role="tablist">
   <button role="tab" aria-selected={vista === 'estadisticas'} className={vista === 'estadisticas' ? 'active' : ''} onClick={() => setVista('estadisticas')}>Estadísticas</button>
   <button role="tab" aria-selected={vista === 'puestos'} className={vista === 'puestos' ? 'active' : ''} onClick={() => setVista('puestos')}>Puestos</button>
  </div>
  {vista === 'estadisticas' ? <Estadisticas clave={clave}/> : <Puestos clave={clave} aptitudes={acceso.aptitudes}/>}
  <p className="subtle">Solo se guarda el resultado de cada evaluación (día, mejor puesto, afinidad, número de brechas y nivel). No se guardan nombres, respuestas ni puntajes por aptitud.</p>
 </section>;
}
