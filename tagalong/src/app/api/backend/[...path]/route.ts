import {NextRequest,NextResponse} from 'next/server';

export const dynamic='force-dynamic';
async function proxy(request:NextRequest, context:{params:Promise<{path:string[]}>}) {
  const base=process.env.FASTAPI_BASE_URL;
  if(!base) return NextResponse.json({detail:'The shared workspace API is not configured.'},{status:503});
  const {path}=await context.params;
  if(path.some(segment=>!segment || segment==='.' || segment==='..' || /[\\/?#]/.test(segment))) return NextResponse.json({detail:'Invalid API path.'},{status:400});
  const authorization=request.headers.get('authorization');
  if(!authorization?.startsWith('Bearer ')) return NextResponse.json({detail:'Sign in to use the shared workspace.'},{status:401});
  const length=Number(request.headers.get('content-length')||0);
  if(length>300_000) return NextResponse.json({detail:'Request is too large.'},{status:413});
  try {
    const body=['GET','HEAD'].includes(request.method)?undefined:await request.text();
    if(body && Buffer.byteLength(body)>300_000) return NextResponse.json({detail:'Request is too large.'},{status:413});
    const target=new URL(base.replace(/\/$/,'')+'/'+path.map(encodeURIComponent).join('/'));
    target.search=request.nextUrl.search;
    const result=await fetch(target,{method:request.method,headers:{Authorization:authorization,'Content-Type':'application/json'},body,cache:'no-store',signal:AbortSignal.timeout(60_000),redirect:'error'});
    const data=await result.text();
    return new NextResponse(data,{status:result.status,headers:{'Content-Type':result.headers.get('content-type')||'application/json','Cache-Control':'no-store'}});
  } catch {return NextResponse.json({detail:'The shared workspace is unavailable. Please try again.'},{status:503});}
}
export {proxy as GET,proxy as POST,proxy as PUT,proxy as DELETE};
