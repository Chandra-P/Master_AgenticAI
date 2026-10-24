import {proxyRequest} from '../../../lib/rag-proxy.mjs';
export async function GET(){const r=await proxyRequest('status',null,process.env);return Response.json(r.data,{status:r.status,headers:{'Cache-Control':'no-store'}});}
