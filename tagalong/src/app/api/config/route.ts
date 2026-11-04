import {NextResponse} from 'next/server';

export const dynamic='force-dynamic';
export function GET() {
  const env=process.env;
  const supabaseUrl=env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey=env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  return NextResponse.json({supabaseUrl,supabaseAnonKey,connectedReady:Boolean(supabaseUrl && supabaseAnonKey && env.FASTAPI_BASE_URL),requireConnected:env.TAGALONG_REQUIRE_CONNECTED==='true'}, {headers:{'Cache-Control':'no-store'}});
}
