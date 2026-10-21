import React, { useState } from 'react';
import { pedirApoyo } from './api.js';

const EJEMPLOS = ['Estoy nervioso por mi entrevista', 'Me rechazaron de otra vacante', 'No puedo dormir pensando en el trabajo'];

// Sección separada de la evaluación: no usa ni cambia el perfil, y no guarda lo que se escribe.
export default function Apoyo() {
 const [texto, setTexto] = useState('');
 const [resultado, setResultado] = useState(null);
 const [cargando, setCargando] = useState(false);
 const [error, setError] = useState('');
 async function enviar(valor) {
  const t = valor.trim();
  if (!t) return;
  setTexto(t); setCargando(true); setError(''); setResultado(null);
  try { setResultado(await pedirApoyo(t)); }
  catch (e) { setError(e.message); }
  finally { setCargando(false); }
 }
 return <section className="knowledge-panel" aria-labelledby="apoyo-titulo">
  <div className="section-title"><p className="eyebrow">APOYO EN LA BÚSQUEDA DE EMPLEO · DATASET KB_limpio.json</p><h3 id="apoyo-titulo">¿Cómo te sientes con tu búsqueda?</h3><p>Escribe en una frase cómo te sientes y te mostramos la respuesta del dataset que más se parece, en español.</p></div>
  <p className="notice"><b>Aviso:</b> esto no es atención profesional. Lo que escribes no se guarda, no se registra y no cambia tu perfil ni tus vacantes recomendadas. Si estás en peligro, llama al 911.</p>
  <form className="knowledge-search" onSubmit={e => { e.preventDefault(); enviar(texto); }}>
   <label htmlFor="apoyo-texto">Cuéntanos<textarea id="apoyo-texto" rows={2} maxLength={500} value={texto} onChange={e => setTexto(e.target.value)} placeholder="Ej. Estoy nervioso por mi entrevista"/></label>
   <button className="button primary" disabled={!texto.trim() || cargando}>{cargando ? 'Buscando…' : 'Enviar →'}</button>
  </form>
  <p className="subtle">{texto.length} / 500 caracteres</p>
  <div className="search-suggestions knowledge-prompts">{EJEMPLOS.map(e => <button className="button secondary" type="button" key={e} onClick={() => enviar(e)}>{e}</button>)}</div>
  {error && <p role="alert" className="error">{error}</p>}
  {resultado && <article className={`card knowledge-answer ${resultado.crisis ? 'crisis' : ''}`} aria-live="polite">
   {resultado.crisis
    ? <><p className="eyebrow">NO ESTÁS SOLO</p><p className="answer-text">{resultado.respuesta}</p><p className="crisis-contact">{resultado.contacto}</p></>
    : <><p className="eyebrow">{resultado.tag ? 'RESPUESTA DEL DATASET' : 'SIN COINCIDENCIA SUFICIENTE'}</p><p className="answer-text">{resultado.respuesta}</p></>}
   {resultado.tag && <details className="ranking"><summary><span>Ver origen</span><span>⌄</span></summary><p>Tema del dataset: <b>{resultado.tag}</b> · similitud {resultado.similitud}</p>{resultado.original && resultado.original !== resultado.respuesta && <blockquote lang="en">{resultado.original}</blockquote>}</details>}
   <p className="subtle">{resultado.aviso}</p>
  </article>}
 </section>;
}
