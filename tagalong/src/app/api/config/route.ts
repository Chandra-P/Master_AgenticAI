import {NextResponse} from 'next/server';

export const dynamic='force-dynamic';
export function GET() {
  const supabaseUrl=process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey=process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  return NextResponse.json({supabaseUrl,supabaseAnonKey,connectedReady:Boolean(supabaseUrl && supabaseAnonKey && process.env.FASTAPI_BASE_URL)}, {headers:{'Cache-Control':'no-store'}});
}
