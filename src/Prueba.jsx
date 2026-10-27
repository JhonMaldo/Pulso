import React, { useState } from 'react';
import { progreso, respondidas } from './logic.js';

// Una pregunta por pantalla con barra de progreso. Las respuestas solo viven en memoria.
export default function Prueba({ prueba, alias, enviando, onTerminar, onCancelar }) {
 const { preguntas, aptitudes, escala } = prueba;
 const [paso, setPaso] = useState(0);
 const [answers, setAnswers] = useState({});
 const p = preguntas[paso];
 const aptitud = aptitudes.find(a => a.id === p.aptitud);
 const total = preguntas.length, hechas = respondidas(preguntas, answers), ultima = paso === total - 1;
 const opciones = p.tipo === 'opcion_multiple' ? p.opciones.map((texto, valor) => ({ texto, valor })) : escala.map((texto, i) => ({ texto, valor: i + 1 }));
 const elegir = valor => setAnswers({ ...answers, [p.id]: valor });

 return <div className="survey">
  <p className="eyebrow">{alias ? `${alias} / ` : ''}PRUEBA DE APTITUDES</p>
  <div className="progress" role="progressbar" aria-label="Avance de la prueba" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progreso(preguntas, answers)}><span style={{ width: `${progreso(preguntas, answers)}%` }}/></div>
  <div className="row"><span className="eyebrow">PREGUNTA {paso + 1} DE {total} · {aptitud?.nombre.toUpperCase()}</span><span className="subtle">{hechas} respondidas</span></div>
  <fieldset key={p.id}>
   <legend>{p.texto}</legend>
   {p.tipo === 'escala' && <p className="subtle">Responde según lo que haces normalmente, no según lo ideal.</p>}
   {opciones.map(o => <label className={`answer ${answers[p.id] === o.valor ? 'selected' : ''}`} key={o.valor}>
    <input type="radio" name={`q${p.id}`} checked={answers[p.id] === o.valor} onChange={() => elegir(o.valor)}/>
    <span>{o.texto}</span>{p.tipo === 'escala' && <b>{o.valor}</b>}
   </label>)}
  </fieldset>
  <div className="bottom-action">
   <button className="button secondary" onClick={() => paso ? setPaso(paso - 1) : onCancelar()}>← {paso ? 'Anterior' : 'Salir'}</button>
   {!ultima
    ? <button className="button primary" disabled={!Number.isInteger(answers[p.id])} onClick={() => setPaso(paso + 1)}>Siguiente →</button>
    : <button className="button primary" disabled={hechas < total || enviando} onClick={() => onTerminar(answers)}>{enviando ? 'Calculando…' : 'Ver mis resultados ↗'}</button>}
  </div>
 </div>;
}
