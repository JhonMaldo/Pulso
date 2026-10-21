import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { QUESTIONS, SKILLS, TEMPLATES, evaluate, searchKnowledge } from '../src/model.js';
const kb = JSON.parse(readFileSync(new URL('../KB_limpio.json', import.meta.url)));
const jobs = TEMPLATES.map((t,i)=>({...t,id:String(i)}));
test('cada aptitud tiene dos preguntas y todos los extremos se normalizan correctamente',()=>{
 for(let i=0;i<SKILLS.length;i++) assert.equal(QUESTIONS.filter(q=>q[1]===i).length,2);
 for(const [answer,expected] of [[1,0],[3,50],[5,100]]) {
  const result=evaluate(Array(12).fill(answer),jobs);
  assert.deepEqual(result.scores,Array(6).fill(expected));
  assert.ok(result.ranking.every(j=>j.score===expected));
 }
});
test('el ranking responde a las prioridades y permite ignorar aptitudes',()=>{
 const a=Array(12).fill(1); a[0]=a[1]=5;
 const result=evaluate(a,[{id:'a',name:'Análisis',weights:[0,5,0,0,0,0]},{id:'b',name:'Comunicación',weights:[5,0,0,0,0,0]}]);
 assert.equal(result.ranking[0].id,'b');assert.equal(result.ranking[0].score,100);
 assert.equal(result.ranking[1].score,0);
 assert.deepEqual(result.strengths,['Comunicación']);assert.equal(result.development.length,5);
});
test('promedia las dos preguntas y calcula el promedio ponderado sin alterar los datos',()=>{
 const answers=[5,3,1,1,1,1,1,1,1,1,1,1];
 const result=evaluate(answers,[{name:'Mixto',weights:[3,1,0,0,0,0]}]);
 assert.equal(result.scores[0],75);assert.equal(result.ranking[0].score,56);
 assert.equal(result.ranking[0].contributions[0].contribution,56.3);
 assert.deepEqual(answers,[5,3,1,1,1,1,1,1,1,1,1,1]);
 assert.deepEqual(result.strengths,['Comunicación']);
});
test('rechaza respuestas incompletas, valores inválidos y vacantes sin prioridades',()=>{
 for(const a of [[],Array(12).fill(null),Array(12).fill(6),Array(12).fill(1.5),Array(12).fill('3')]) assert.throws(()=>evaluate(a,jobs));
 for(const j of [[],[{name:'X',weights:[0,0,0,0,0,0]}],[{name:'',weights:[1,1,1,1,1,1]}],[{name:'X',weights:[1]}],[{name:'X',weights:[6,1,1,1,1,1]}]]) assert.throws(()=>evaluate(Array(12).fill(3),j));
});
test('los empates son deterministas sin alterar el orden de las vacantes originales',()=>{
 const original=jobs.map(j=>j.id); const r=evaluate(Array(12).fill(3),jobs);
 assert.deepEqual(jobs.map(j=>j.id),original);
 assert.deepEqual(r.ranking.map(j=>j.name),jobs.map(j=>j.name).sort((a,b)=>a.localeCompare(b)));
});
test('utiliza el dataset real y devuelve ejemplos verificables, sin inventar coincidencias',()=>{
 assert.equal(kb.intents.length,79);
 assert.ok(kb.intents.every(i=>typeof i.tag==='string'&&Array.isArray(i.patterns)&&Array.isArray(i.responses)));
 assert.deepEqual(searchKnowledge(kb,''),[]);
 assert.deepEqual(searchKnowledge(kb,'zzzxxyyunknown'),[]);
 assert.deepEqual(searchKnowledge(kb,' HELLO '),searchKnowledge(kb,'hello'));
 const found=searchKnowledge(kb,'work');assert.ok(found.length>0&&found.length<=8);
 for(const r of found) assert.ok(r.examples.every(p=>kb.intents.find(i=>i.tag===r.tag).patterns.includes(p)));
});
