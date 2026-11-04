import { useCallback, useEffect, useState } from 'react';
export async function api<T>(path:string, options?:RequestInit):Promise<T> {
 const response=await fetch(`/api/${path}`,{...options,headers:options?.body instanceof FormData ? options.headers : {'Content-Type':'application/json',...options?.headers}});
 if (!response.ok) {
  const data=await response.json().catch(()=>({detail:'The service is unavailable. Please try again.'}));
  throw new Error(typeof data.detail==='string'?data.detail:'Please check the form values and try again.');
 }
 return response.json() as Promise<T>;
}
export function useResource<T>(path:string) {
 const [data,setData]=useState<T|null>(null);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState<string|null>(null);
 const refresh=useCallback(()=>{
  setLoading(true);setError(null);
  return api<T>(path).then(setData).catch(e=>setError(e.message)).finally(()=>setLoading(false));
 },[path]);
 useEffect(()=>{void refresh();},[refresh]);
 return {data,loading,error,refresh,setData};
}
