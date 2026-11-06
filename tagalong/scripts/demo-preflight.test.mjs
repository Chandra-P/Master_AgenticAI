import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

const target=new URL('./demo-preflight.mjs',import.meta.url).href;
for(const item of [
 {name:'rejects an unconfigured frontend',frontend:false,assistant:true,expected:1},
 {name:'rejects an API without its assistant',frontend:true,assistant:false,expected:1},
 {name:'accepts connected frontend and configured API',frontend:true,assistant:true,expected:0},
])test(item.name,()=>{
 const code=`globalThis.fetch=async url=>({ok:true,status:200,json:async()=>url.endsWith('/health')?{status:'ok',capabilities:{plans:true,assistant:${item.assistant}}}:{connectedReady:${item.frontend}}});await import(${JSON.stringify(target)});`;
 const result=spawnSync(process.execPath,['--input-type=module','-e',code],{encoding:'utf8'});
 assert.equal(result.status,item.expected,result.stdout+'\n'+result.stderr);
});
