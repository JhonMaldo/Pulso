import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildKnowledge, findKnowledge } from '../src/knowledge.js';
const source=JSON.parse(readFileSync(new URL('../KB_limpio.json',import.meta.url)));
const spanish=JSON.parse(readFileSync(new URL('../src/data/KB_es.json',import.meta.url)));
const entries=buildKnowledge(source,spanish);

test('cada tema traducido corresponde a una intención real sin duplicados ni referencias rotas',()=>{
 assert.equal(entries.length,79);
 assert.deepEqual(new Set(spanish.intents.map(e=>e.tag)),new Set(source.intents.map(e=>e.tag)));
 assert.equal(new Set(spanish.intents.map(e=>e.tag)).size,spanish.intents.length);
 assert.equal(entries.reduce((n,e)=>n+e.patterns.length,0),128);
 for(const entry of entries){
  const original=source.intents.find(e=>e.tag===entry.tag);
  assert.ok(entry.patterns.length>=1&&entry.responses.length>=1);
  assert.equal(new Set(entry.patterns.map(p=>p.sourceIndex)).size,entry.patterns.length);
  for(const p of entry.patterns){assert.ok(p.text.trim());assert.equal(p.original,original.patterns[p.sourceIndex]);}
  for(const r of entry.responses){assert.equal(r.original,original.responses[r.sourceIndex]);assert.ok(['traducción','resumen adaptado'].includes(r.kind));}
 }
});
test('las preguntas traducidas recuperan su fuente en español y en inglés',()=>{
 for(const tag of ['stressed','happy','sleep','fact-1','fact-31']){
  const e=entries.find(e=>e.tag===tag);
  assert.equal(findKnowledge(entries,e.patterns[0].text)[0].entry.tag,tag);
  assert.equal(findKnowledge(entries,e.originalPatterns[0])[0].entry.tag,tag);
 }
 assert.equal(findKnowledge(entries,'   NO PUEDO DORMIR!! ')[0].entry.tag,'sleep');
 assert.equal(findKnowledge(entries,'Estoy bajo mucha presion')[0].entry.tag,'stressed');
 assert.equal(findKnowledge(entries,'Me siento triste')[0].entry.tag,'sad');
});
test('no inventa respuestas con consultas vacías, genéricas o sin coincidencias',()=>{
 for(const q of ['', ' ', 'xyzunknown123','¿qué?', 'yo me siento']) assert.deepEqual(findKnowledge(entries,q),[]);
 assert.ok(findKnowledge(entries,'estrés').length>0);
 assert.ok(findKnowledge(entries,'salud mental').length<=8);
});
test('los originales se resuelven desde el dataset y no están duplicados en el archivo de traducciones',()=>{
 const changed=structuredClone(source);
 changed.intents[0].responses[0]='Nueva respuesta de la fuente';
 assert.equal(buildKnowledge(changed,spanish)[0].responses[0].original,'Nueva respuesta de la fuente');
 assert.equal(entries[0].responses[0].original,source.intents[0].responses[0]);
 assert.ok(spanish.intents.every(e=>e.responses.every(r=>!('original' in r))));
});
test('una traducción con un índice inexistente falla de manera explícita',()=>{
 const bad=structuredClone(spanish);bad.intents[0].patterns[0].sourceIndex=999999;
 assert.throws(()=>buildKnowledge(source,bad),/Referencia de pregunta inválida/);
});
