import { NextRequest, NextResponse } from 'next/server';
const limit=2*1024*1024+65536;
async function proxy(request:NextRequest,{params}:{params:Promise<{path:string[]}>}) {
 const {path}=await params;
 const backend=process.env.API_URL||'http://127.0.0.1:8000';
 const url=new URL(`/api/${path.map(encodeURIComponent).join('/')}`,backend);
 url.search=request.nextUrl.search;
 const headers:Record<string,string>={};
 const type=request.headers.get('content-type');if(type)headers['content-type']=type;
 if(process.env.FINPILOT_ACCESS_TOKEN)headers.authorization=`Bearer ${process.env.FINPILOT_ACCESS_TOKEN}`;
 if(Number(request.headers.get('content-length')||0)>limit)return NextResponse.json({detail:'Request exceeds the upload limit'},{status:413});
 try{
  const body=['GET','HEAD'].includes(request.method)?undefined:await request.arrayBuffer();
  if(body&&body.byteLength>limit)return NextResponse.json({detail:'Request exceeds the upload limit'},{status:413});
  const response=await fetch(url,{method:request.method,headers,body,cache:'no-store',signal:AbortSignal.timeout(90000)});
  return new NextResponse(await response.arrayBuffer(),{status:response.status,headers:{'content-type':response.headers.get('content-type')||'application/json','cache-control':'no-store'}});
 }catch{
  return NextResponse.json({detail:'The financial service is unavailable. Check that the FastAPI backend is running.'},{status:503});
 }
}
export {proxy as GET,proxy as POST,proxy as PUT};
