import {NextResponse} from 'next/server';
export const dynamic='force-dynamic';
export async function GET(){
 const env=process.env;
 if(env.TAGALONG_REQUIRE_CONNECTED!=='true')return NextResponse.json({status:'ok',mode:'demo-available'});
 if(!env.FASTAPI_BASE_URL||!env.NEXT_PUBLIC_SUPABASE_URL||!env.NEXT_PUBLIC_SUPABASE_ANON_KEY)return NextResponse.json({status:'unconfigured'},{status:503});
 try{const response=await fetch(env.FASTAPI_BASE_URL.replace(/\/$/,'')+'/health',{cache:'no-store',signal:AbortSignal.timeout(5000)});const data=await response.json();if(!response.ok||data.status!=='ok')throw new Error();return NextResponse.json({status:'ok',mode:'connected'});}
 catch{return NextResponse.json({status:'unavailable'},{status:503});}
}
