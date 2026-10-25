export function normalizePayload(p){
 if(typeof p.question!=='string'||p.question.trim().length<3||p.question.length>1200)throw Error('Invalid question');
 const strategy=p.strategy??'semantic',charter=p.charter??'',year=String(p.year??'');
 if(!['fixed','semantic'].includes(strategy)||typeof charter!=='string'||(charter&&!/^\d{1,5}$/.test(charter))||(year&&!['2021','2022','2023','2024','2025'].includes(year)))throw Error('Invalid filters');
 return {question:p.question.trim(),strategy,charter,year,rerank:p.rerank!==false};
}
export async function proxyRequest(action,payload,env,visitor='anonymous'){
 if(!env.RAG_BACKEND_URL)return {status:503,data:{ready:false,generation:false,error:'The live backend is not connected. Source documents and measured experiments remain available.'}};
 try{
  const url=new URL(env.RAG_BACKEND_URL);if(url.protocol!=='https:'&&!(url.protocol==='http:'&&url.hostname==='127.0.0.1'))throw Error('Invalid backend');
  const timeout=action==='status'?10000:Number(env.RAG_BACKEND_TIMEOUT_MS??600000);
  if(!Number.isInteger(timeout)||timeout<1000||timeout>900000)throw Error('Invalid backend timeout');
  const r=await fetch(new URL('/api/'+(action==='status'?'status':'ask'),url),{method:action==='status'?'GET':'POST',headers:{'Content-Type':'application/json',...(env.RAG_BACKEND_TOKEN?{'Authorization':'Bearer '+env.RAG_BACKEND_TOKEN}:{}),'X-Visitor-Id':visitor},...(action==='status'?{}:{body:JSON.stringify(normalizePayload(payload))}),signal:AbortSignal.timeout(timeout)});
  const text=await r.text();if(text.length>120000)throw Error('Oversized response');return {status:r.status,data:JSON.parse(text)};
 }catch{return {status:503,data:{ready:false,generation:false,error:'The research backend is temporarily offline. Please explore the source library or experiment results.'}};}
}
