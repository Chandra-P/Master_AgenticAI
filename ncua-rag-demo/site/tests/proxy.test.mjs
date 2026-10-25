import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizePayload,proxyRequest} from '../lib/rag-proxy.mjs';

test('rejects oversized questions and invalid collection strategies',()=>{
  assert.throws(()=>normalizePayload({question:'x'.repeat(1201)}));
  assert.throws(()=>normalizePayload({question:'assets',strategy:'arbitrary'}));
});
test('does not allow visitors to provide backend URL or secrets',()=>{
  const p=normalizePayload({question:'assets',backend:'https://attacker.invalid',token:'secret',charter:'5536'});
  assert.equal(p.backend,undefined);assert.equal(p.token,undefined);assert.equal(p.charter,'5536');
});
test('missing backend returns clear setup state without pretending to retrieve',async()=>{
  const r=await proxyRequest('status',null,{});
  assert.equal(r.status,503);assert.equal(r.data.ready,false);
  assert.equal(r.data.generation,false);
});

test('local inference gets a longer bounded timeout than status requests',async(t)=>{
  const delays=[];
  t.mock.method(AbortSignal,'timeout',ms=>{delays.push(ms);return new AbortController().signal;});
  t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify({ready:true}),{status:200}));
  const env={RAG_BACKEND_URL:'http://127.0.0.1:8765'};
  assert.equal((await proxyRequest('ask',{question:'assets'},env)).status,200);
  await proxyRequest('status',null,env);
  assert.deepEqual(delays,[600000,10000]);
});
