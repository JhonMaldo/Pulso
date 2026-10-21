import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { evaluar, obtenerPrueba } from './api.js';
import { armarRespuestas } from './logic.js';
import Prueba from './Prueba.jsx';
import { Detalle, Resultados } from './Resultados.jsx';
import Apoyo from './Apoyo.jsx';
import './styles.css';

const AVISO = 'Esta prueba es una orientación, no una evaluación profesional, y no decide una contratación. Tus respuestas no se asocian con tu nombre.';

function App() {
 const [vista, setVista] = useState('inicio');
 const [alias, setAlias] = useState('');
 const [prueba, setPrueba] = useState(null);
 const [resultado, setResultado] = useState(null);
 const [detalle, setDetalle] = useState(null);
 const [explicaciones, setExplicaciones] = useState({});
 const [cargando, setCargando] = useState(false);
 const [error, setError] = useState('');

 function ir(v) { setVista(v); setError(''); window.scrollTo?.({ top: 0 }); }
 async function empezar() {
  setCargando(true); setError('');
  try { setPrueba(prueba || await obtenerPrueba()); ir('prueba'); }
  catch (e) { setError(e.message); }
  finally { setCargando(false); }
 }
 async function terminar(answers) {
  setCargando(true); setError('');
  try { setResultado(await evaluar(armarRespuestas(prueba.preguntas, answers))); setExplicaciones({}); ir('resultados'); }
  catch (e) { setError(e.message); }
  finally { setCargando(false); }
 }
 function reiniciar() { setResultado(null); setDetalle(null); setExplicaciones({}); ir('inicio'); }
 const enEvaluacion = vista !== 'apoyo';

 return <>
  <header><a className="brand" href="#inicio" onClick={reiniciar}>p<span className="brand-symbol">↗</span> pulso<span className="brand-dot">.</span></a><span className="header-note">APTITUDES Y VACANTES</span><span className="local-badge">● Sin registro</span></header>
  <main id="inicio">
   <nav className="tabs main-tabs" aria-label="Secciones">
    <button className={enEvaluacion ? 'active' : ''} aria-current={enEvaluacion ? 'page' : undefined} onClick={() => ir(resultado ? 'resultados' : prueba && vista === 'prueba' ? 'prueba' : 'inicio')}><span>01</span>Evaluación de aptitudes</button>
    <button className={!enEvaluacion ? 'active' : ''} aria-current={!enEvaluacion ? 'page' : undefined} onClick={() => ir('apoyo')}><span>02</span>Apoyo en la búsqueda de empleo</button>
   </nav>
   {error && <p role="alert" className="error">{error}</p>}

   {vista === 'inicio' && <section className="hero">
    <div>
     <p className="eyebrow">DEL POTENCIAL A LA OPORTUNIDAD</p>
     <h1>Conoce tus aptitudes y<br/>las vacantes que <em>encajan contigo.</em></h1>
     <p className="intro">Contesta 24 preguntas (unos 10 minutos). Calculamos tu perfil en 8 aptitudes, te mostramos las 5 vacantes más afines y, si quieres, una IA te explica por qué.</p>
     <p className="notice" role="note"><b>Aviso de uso:</b> {AVISO} Las preguntas de escala son autoevaluación, así que el resultado es indicativo.</p>
     <label>Nombre o alias (opcional)<input maxLength={40} value={alias} onChange={e => setAlias(e.target.value)} placeholder="Ej. Candidato 01" autoComplete="off"/></label>
     <p className="subtle">El alias solo se muestra en esta pantalla; no se envía al servidor. No pedimos correo, teléfono ni dirección.</p>
     <button className="button primary" onClick={empezar} disabled={cargando}>{cargando ? 'Cargando…' : 'Empezar la prueba'} <span>↗</span></button>
    </div>
    <aside className="hero-card"><span className="eyebrow">CÓMO FUNCIONA</span>{[['01', 'Contestas la prueba', 'Opción múltiple y escala del 1 al 5, una pregunta por pantalla.'], ['02', 'El motor calcula', 'Tu perfil de 0 a 100 y tu afinidad con 20 vacantes de ejemplo, con una fórmula clara.'], ['03', 'La IA explica', 'Con «¿Por qué?», Ollama consulta al motor con sus herramientas y lo explica en palabras sencillas.']].map(([n, t, d]) => <div className="journey" key={n}><span>{n}</span><div><h3>{t}</h3><p>{d}</p></div></div>)}</aside>
   </section>}

   {vista === 'prueba' && prueba && <section className="workspace"><div className="workspace-body"><Prueba prueba={prueba} alias={alias.trim()} enviando={cargando} onTerminar={terminar} onCancelar={() => ir('inicio')}/></div></section>}
   {vista === 'resultados' && resultado && <section className="workspace"><div className="workspace-body"><Resultados resultado={resultado} aptitudes={prueba.aptitudes} alias={alias.trim()} onDetalle={r => { setDetalle(r); ir('detalle'); }} onReiniciar={reiniciar}/></div></section>}
   {vista === 'detalle' && detalle && <section className="workspace"><div className="workspace-body"><Detalle rec={detalle} perfil={resultado.perfil} aptitudes={prueba.aptitudes} explicacion={explicaciones[detalle.vacante.id]} onExplicacion={(id, e) => setExplicaciones(x => ({ ...x, [id]: e }))} onVolver={() => ir('resultados')}/></div></section>}
   {vista === 'apoyo' && <section className="workspace"><div className="workspace-body"><Apoyo/></div></section>}

   <section className="limits"><span className="eyebrow">USO RESPONSABLE</span><h2>Una orientación.<br/><em>El criterio sigue siendo humano.</em></h2><p>{AVISO} No usamos edad, género, estado civil ni origen. La IA no calcula ni cambia puntajes: solo explica lo que calcula el motor. Las vacantes son datos de ejemplo.</p></section>
  </main>
  <footer><a className="brand" href="#inicio">pulso.</a><p>Aptitudes y vacantes.</p><span>Proyecto académico · Inteligencia Artificial · 2026</span></footer>
 </>;
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
