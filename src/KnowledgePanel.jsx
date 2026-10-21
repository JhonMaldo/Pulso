import React, { useMemo, useState } from 'react';
import source from '../KB_limpio.json';
import spanish from './data/KB_es.json';
import { buildKnowledge, findKnowledge } from './knowledge';

const entries = buildKnowledge(source,spanish);
const translatedCount = entries.reduce((n,e)=>n+e.patterns.length,0);
const prompts = ['¿Qué es la salud mental?','Estoy bajo mucha presión','No puedo dormir','¿Cuál es la diferencia entre la ansiedad y el estrés?'];
export default function KnowledgePanel({onReturn}) {
 const [query,setQuery] = useState('');
 const [asked,setAsked] = useState('');
 const [selected,setSelected] = useState(null);
 const [topic,setTopic] = useState('');
 const matches = useMemo(()=>findKnowledge(entries,asked),[asked]);
 const entry = entries.find(e=>e.tag===selected);
 function ask(text) {
  const value=text.trim();setQuery(value);setAsked(value);setTopic('');
  const found=findKnowledge(entries,value);
  // Automatically open only a full exact example; other matches require choosing a topic.
  setSelected(found[0]?.score===4?found[0].entry.tag:null);
 }
 function browse(tag) {setSelected(tag||null);setTopic(tag);setAsked('');}
 return <section className="knowledge-panel" aria-label="Consulta del dataset en español">
 <div className="section-title"><p className="eyebrow">CONSULTA EN ESPAÑOL / KB_limpio.json</p><h3>Pregunta. Explora. Comprende.</h3><p>Consulta información del archivo original con traducciones al español. Puedes escribir una pregunta o elegir un tema.</p></div>
 <div className="data-stats">{[[entries.length,'temas disponibles'],[translatedCount,'frases traducidas'],[entries.reduce((n,e)=>n+e.responses.length,0),'respuestas traducidas o resumidas']].map(([n,label])=><div key={label} className="card"><strong>{n}</strong><span>{label}</span></div>)}</div>
 <form className="knowledge-search" onSubmit={e=>{e.preventDefault();ask(query)}}><label htmlFor="knowledge-query">¿Qué te gustaría consultar?<input id="knowledge-query" type="search" required maxLength={300} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ej. Me siento triste, estrés, ¿qué es la terapia?"/></label><button className="button primary" disabled={!query.trim()}>Consultar →</button></form>
 <div className="search-suggestions knowledge-prompts">{prompts.map(p=><button className="button secondary" type="button" key={p} onClick={()=>ask(p)}>{p}</button>)}</div>
 <label>O elige uno de los {entries.length} temas<select value={topic} onChange={e=>browse(e.target.value)}><option value="">Seleccionar tema…</option>{entries.map(e=><option value={e.tag} key={e.tag}>{e.label}</option>)}</select></label>
 {asked&&<div className="knowledge-matches"><p role="status">{matches.length?`Encontré ${matches.length} temas relacionados. Selecciona el que quieras consultar.`:'No encontré una coincidencia suficiente. Prueba una frase sugerida o elige un tema del catálogo.'}</p>{matches.map(m=><button type="button" key={m.entry.tag} className={`knowledge-match ${selected===m.entry.tag?'chosen':''}`} onClick={()=>setSelected(m.entry.tag)}><span>{m.entry.label}<small>{m.match}</small></span><span>↗</span></button>)}</div>}
 {entry&&<article className="card knowledge-answer" aria-live="polite"><p className="eyebrow">INFORMACIÓN RECUPERADA DEL DATASET</p><h3>{entry.label}</h3><div className="source-question"><span>Ejemplo traducido</span><p>{entry.patterns[0]?.text||entry.originalPatterns[0]}</p></div>{entry.responses.map(r=><div key={r.sourceIndex}><span className="translation-badge">{r.kind==='traducción'?'Traducción al español':'Resumen adaptado en español'}</span><p className="answer-text">{r.text}</p></div>)}
 {['about','skill','creation','name','location','done'].includes(entry.tag)&&<p className="notice">Este texto describe al asistente del dataset original. Es una cita traducida; no describe las capacidades, autoría ni almacenamiento de Pulso.</p>}
 {entry.tag==='mental-health-fact'&&<p className="notice">El archivo no incluye fecha ni enlace para verificar esta cifra. Se muestra como contenido de la fuente, no como estadística vigente.</p>}
 <details className="ranking"><summary><span>Ver original y procedencia</span><span>⌄</span></summary><p><b>Archivo:</b> KB_limpio.json<br/><b>Intención:</b> {entry.tag}<br/><b>Pregunta:</b> patterns[{entry.patterns[0]?.sourceIndex??0}]<br/><b>Respuesta:</b> responses[0]</p><p lang="en">{entry.originalPatterns[entry.patterns[0]?.sourceIndex??0]}</p><blockquote lang={entry.tag==='suicide'?'es':'en'}>{entry.originalResponses[0]}</blockquote></details>
 <details className="ranking"><summary><span>Más frases de este tema</span><span>{entry.patterns.length} traducidas ⌄</span></summary>{entry.patterns.map(p=><div className="parallel-example" key={p.sourceIndex}><p>{p.text}</p><small lang="en">{p.original}</small></div>)}<p className="subtle">{entry.patterns.length} de {entry.originalPatterns.length} ejemplos traducidos. La traducción es parcial.</p></details>
 </article>}
 <p className="subtle">Contenido educativo de una base conversacional. La búsqueda compara palabras y ejemplos; no es una conversación con un modelo de IA ni realiza diagnósticos. Las consultas no se incluyen en el reporte del candidato ni afectan la afinidad de los puestos.</p>
 <p className="subtle">Traducción parcial: se cubren los 79 temas con al menos una frase y una respuesta por tema; los textos largos se identifican como resúmenes. El archivo original se conserva íntegro.</p>
 {onReturn&&<button type="button" className="button secondary" onClick={onReturn}>← Volver a mi encuesta</button>}
 </section>;
}
