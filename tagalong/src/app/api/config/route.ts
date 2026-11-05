import {NextResponse} from 'next/server';

export const dynamic='force-dynamic';
export function GET() {
  // Reflective lookup keeps standalone configuration runtime-based under Turbopack.
  const read=(name:string):string=>Reflect.get(process.env,name)||'';
  const supabaseUrl=read('NEXT_PUBLIC_SUPABASE_URL');
  const supabaseAnonKey=read('NEXT_PUBLIC_SUPABASE_ANON_KEY');
  return NextResponse.json({supabaseUrl,supabaseAnonKey,connectedReady:Boolean(supabaseUrl && supabaseAnonKey && read('FASTAPI_BASE_URL')),requireConnected:read('TAGALONG_REQUIRE_CONNECTED')==='true'}, {headers:{'Cache-Control':'no-store'}});
}
