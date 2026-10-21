export const SKILLS = ['Comunicación', 'Análisis', 'Organización', 'Trabajo en equipo', 'Liderazgo', 'Creatividad'];
export const QUESTIONS = [
 ['Explico una idea compleja con ejemplos y compruebo que se entendió.', 0],
 ['Escucho una necesidad y adapto mi forma de comunicar la solución.', 0],
 ['Comparo datos y alternativas antes de tomar una decisión.', 1],
 ['Divido un problema en partes y verifico sus posibles causas.', 1],
 ['Ordeno mis pendientes por prioridad y cumplo los plazos acordados.', 2],
 ['Reviso los detalles de una tarea antes de entregarla.', 2],
 ['Comparto información y ayudo al equipo a resolver bloqueos.', 3],
 ['Busco acuerdos cuando existen opiniones distintas.', 3],
 ['Coordino tareas y doy seguimiento a los acuerdos del equipo.', 4],
 ['Puedo dar retroalimentación concreta y respetuosa.', 4],
 ['Propongo alternativas cuando la solución habitual no funciona.', 5],
 ['Convierto una idea nueva en una propuesta que se pueda probar.', 5],
];
export const TEMPLATES = [
 { name: 'Atención al cliente', weights: [5, 2, 3, 4, 1, 2] },
 { name: 'Analista de datos', weights: [2, 5, 4, 3, 1, 2] },
 { name: 'Coordinación de proyectos', weights: [4, 3, 5, 4, 5, 2] },
 { name: 'Diseño y contenido', weights: [4, 2, 3, 3, 1, 5] },
];
export function evaluate(answers, jobs) {
 if (!Array.isArray(answers) || answers.length !== QUESTIONS.length || answers.some(a => !Number.isInteger(a) || a < 1 || a > 5)) throw new Error('Responde las 12 preguntas.');
 if (!Array.isArray(jobs) || !jobs.length) throw new Error('Agrega al menos una vacante.');
 const scores = SKILLS.map((_, i) => Math.round(QUESTIONS.reduce((sum, q, j) => sum + (q[1] === i ? (answers[j] - 1) * 25 : 0), 0) / QUESTIONS.filter(q => q[1] === i).length));
 const ranking = jobs.map(job => {
  if (!job.name?.trim() || job.weights?.length !== SKILLS.length || job.weights.some(w => !Number.isInteger(w) || w < 0 || w > 5) || !job.weights.some(w => w > 0)) throw new Error('La vacante necesita un nombre y al menos una prioridad mayor que cero.');
  const total = job.weights.reduce((a,b) => a+b,0);
  return { ...job, score: Math.round(scores.reduce((sum, s, i) => sum+s*job.weights[i],0)/total), contributions: SKILLS.map((name,i) => ({name, weight: job.weights[i], score: scores[i], contribution: Math.round(scores[i]*job.weights[i]/total*10)/10})) };
 }).sort((a,b) => b.score-a.score || a.name.localeCompare(b.name));
 return { scores, ranking, strengths: SKILLS.filter((_,i) => scores[i] >= 75), development: SKILLS.filter((_,i) => scores[i] < 50) };
}
export const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim();
export function searchKnowledge(dataset, query) {
 const q = normalize(query);
 if (!q) return [];
 // Retrieval of source examples only: no diagnosis, inferred aptitude or generated advice.
 return dataset.intents.map(intent => {
  const examples = intent.patterns.filter(p => normalize(p).includes(q));
  return { tag: intent.tag, examples, count: examples.length };
 }).filter(r => r.count).sort((a,b) => b.count-a.count || a.tag.localeCompare(b.tag)).slice(0,8);
}
