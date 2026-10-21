import { normalize } from './logic.js';

// Source indexes are resolved against the actual KB: translations never create new intents.
export function buildKnowledge(source, spanish) {
 return source.intents.map(intent => {
  const local = spanish.intents.find(item => item.tag === intent.tag);
  const patterns = (local?.patterns || []).map(item => {
   if (typeof intent.patterns[item.sourceIndex] !== 'string') throw new Error(`Referencia de pregunta inválida: ${intent.tag}`);
   return { ...item, original: intent.patterns[item.sourceIndex] };
  });
  const responses = (local?.responses || []).map(item => {
   if (typeof intent.responses[item.sourceIndex] !== 'string') throw new Error(`Referencia de respuesta inválida: ${intent.tag}`);
   return { ...item, original: intent.responses[item.sourceIndex] };
  });
  return { tag: intent.tag, label: local?.label || intent.tag, patterns, responses, originalPatterns: intent.patterns, originalResponses: intent.responses };
 });
}
const STOP = new Set('a al algo de del el en es esta este estoy la las lo los me mi mis muy para por que se si siento sobre tengo un una y yo como cual cuales the i am is what how are feel feeling'.split(' '));
const tokens = text => [...new Set(normalize(text).split(' ').filter(t=>t.length>1&&!STOP.has(t)))];

export function findKnowledge(entries, query) {
 const q = normalize(query);
 if (!q) return [];
 const words = tokens(query);
 return entries.map(entry => {
  // Match a full example, a title, or the text of a response, in either language.
  const texts = [entry.label, entry.tag, ...entry.patterns.map(p=>p.text), ...entry.originalPatterns];
  const normalized = texts.map(normalize);
  const exact = normalized.some(t=>t===q);
  const phrase = words.length>0 && normalized.some(t=>t.includes(q));
  const vocabulary = new Set(normalized.flatMap(t=>t.split(' ')));
  const matched = words.filter(w=>vocabulary.has(w)).length;
  const coverage = words.length ? matched/words.length : 0;
  // Single common words never guess an intent. A partial match is offered as a topic, not a diagnosis.
  const responseMatch = words.length>0 && q.length>=4 && [...entry.responses.map(r=>r.text),...entry.originalResponses].some(t=>normalize(t).includes(q));
  const score = exact ? 4 : phrase ? 3 : coverage>=0.6&&matched>=2 ? 1+coverage : responseMatch ? .5 : 0;
  return { entry, score, match: exact?'Ejemplo exacto':phrase?'Coincidencia de texto':score>=1?'Palabras en común':'Coincidencia en una respuesta' };
 }).filter(r=>r.score>0).sort((a,b)=>b.score-a.score||a.entry.label.localeCompare(b.entry.label,'es')).slice(0,8);
}
