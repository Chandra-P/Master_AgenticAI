import {NextRequest,NextResponse} from 'next/server';

export const dynamic='force-dynamic';
async function proxy(request:NextRequest, context:{params:Promise<{path:string[]}>}) {
  const base=process.env.FASTAPI_BASE_URL;
  if(!base) return NextResponse.json({detail:'The shared workspace API is not configured.'},{status:503});
  const {path}=await context.params;
  if(path.some(segment=>!segment || segment==='.' || segment==='..' || /[\\/?#]/.test(segment))) return NextResponse.json({detail:'Invalid API path.'},{status:400});
  const authorization=request.headers.get('authorization');
  const publicAustinDemo=request.method==='GET'&&path.length===4&&path[0]==='v1'&&path[1]==='public'&&path[2]==='demo-stories'&&path[3]==='austin-four-friends';
  if(!authorization?.startsWith('Bearer ')&&!publicAustinDemo) return NextResponse.json({detail:'Sign in to use the shared workspace.'},{status:401});
  const length=Number(request.headers.get('content-length')||0);
  if(length>300_000) return NextResponse.json({detail:'Request is too large.'},{status:413});
  try {
    const body=['GET','HEAD'].includes(request.method)?undefined:await request.text();
    if(body && Buffer.byteLength(body)>300_000) return NextResponse.json({detail:'Request is too large.'},{status:413});
    const target=new URL(base.replace(/\/$/,'')+'/'+path.map(encodeURIComponent).join('/'));
    target.search=request.nextUrl.search;
    const workspaceMode=request.headers.get('x-workspace-mode')==='admin'?'admin':'member';
    const headers:Record<string,string>={'Content-Type':'application/json','X-Workspace-Mode':workspaceMode};
    if(authorization?.startsWith('Bearer '))headers.Authorization=authorization;
    const result=await fetch(target,{method:request.method,headers,body,cache:'no-store',signal:AbortSignal.timeout(60_000),redirect:'error'});
    const data=await result.text();
    return new NextResponse(data,{status:result.status,headers:{'Content-Type':result.headers.get('content-type')||'application/json','Cache-Control':publicAustinDemo?'public, max-age=300':'no-store'}});
  } catch {return NextResponse.json({detail:'The shared workspace is unavailable. Please try again.'},{status:503});}
}
export {proxy as GET,proxy as POST,proxy as PUT,proxy as PATCH,proxy as DELETE};
