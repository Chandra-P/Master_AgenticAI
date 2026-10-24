import {normalizePayload,proxyRequest} from '../../../lib/rag-proxy.mjs';
export async function POST(request:Request){
 try{const text=await request.text();if(text.length>8000)return Response.json({error:'Request too large'},{status:413});const p=normalizePayload(JSON.parse(text));const r=await proxyRequest('ask',p,process.env,request.headers.get('cf-connecting-ip')??'anonymous');return Response.json(r.data,{status:r.status,headers:{'Cache-Control':'no-store'}});}
 catch{return Response.json({error:'Please enter a valid question and filters.'},{status:400});}
}
