/** Render only public links; never load a saved image from a local/private host. */
export function publicWebUrl(value:string|null|undefined,httpsOnly=false):string|undefined {
 try{
  const url=new URL(value||'');const host=url.hostname.toLowerCase();
  if(!(httpsOnly?url.protocol==='https:':['http:','https:'].includes(url.protocol))||url.username||url.password||url.port&&!['80','443'].includes(url.port))return;
  if(!host.includes('.')||host==='localhost'||/\.(?:local|internal|localhost)$/.test(host)||host.includes(':'))return;
  if(/^\d+(?:\.\d+){3}$/.test(host)){const [a,b]=host.split('.').map(Number);if(a===0||a===10||a===127||a===169&&b===254||a===172&&b>=16&&b<=31||a===192&&b===168||a===100&&b>=64&&b<=127||a>=224)return;}
  return url.href;
 }catch{return;}
}
export function safeActivityImage(value:string|undefined){if(value?.startsWith('/images/')&&!value.includes('..')&&/^\/[\w/.-]+$/.test(value))return value;return publicWebUrl(value,true);}
