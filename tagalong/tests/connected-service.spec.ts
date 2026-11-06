import {test,expect} from '@playwright/test';
import type {SupabaseClient} from '@supabase/supabase-js';
import {ConnectedService} from '../src/services/connected';

const auth={auth:{getSession:async()=>({data:{session:{access_token:'synthetic-token',user:{id:'test'}}},error:null})}} as unknown as SupabaseClient;

test('read retries once after a temporary HTML response, while writes never retry',async()=>{
 const original=globalThis.fetch;
 try{
  let calls=0;
  globalThis.fetch=async()=>++calls===1?new Response('<html>Starting</html>',{status:503}):Response.json({ready:true});
  await expect(new ConnectedService(auth).request('/v1/me')).resolves.toEqual({ready:true});
  expect(calls).toBe(2);
  calls=0;
  globalThis.fetch=async()=>{calls++;return new Response('<html>Unavailable</html>',{status:502});};
  await expect(new ConnectedService(auth).request('/v1/plans',{method:'POST',body:'{}'})).rejects.toThrow('Shared workspace is temporarily unavailable. Please wait a moment and try again.');
  expect(calls).toBe(1);
 }finally{globalThis.fetch=original;}
});

test('malformed successful responses fail clearly after at most one read retry',async()=>{
 const original=globalThis.fetch;
 try{
  let calls=0;
  globalThis.fetch=async()=>{calls++;return new Response('not JSON',{status:200});};
  await expect(new ConnectedService(auth).request('/v1/plans')).rejects.toThrow('Shared workspace is temporarily unavailable. Please wait a moment and try again.');
  expect(calls).toBe(2);
 }finally{globalThis.fetch=original;}
});
