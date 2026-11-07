import {expect,type Page,type TestInfo} from '@playwright/test';

export async function inspectVisual(page:Page,info:TestInfo,name:string){
 // Wait for visible images before measuring/capturing a newly selected tool.
 await page.evaluate(()=>Promise.race([Promise.all([...document.images].filter(image=>{const box=image.getBoundingClientRect();return box.top<innerHeight&&box.bottom>0;}).map(image=>image.decode().catch(()=>{}))),new Promise(resolve=>setTimeout(resolve,2000))]));
 const issues=await page.evaluate(()=>{
  type Color=[number,number,number,number];
  function color(value:string):Color{const n=value.match(/[\d.]+/g)?.map(Number)||[0,0,0,0];return [n[0],n[1],n[2],n[3]??1];}
  function blend(top:Color,bottom:Color):Color{const a=top[3]+bottom[3]*(1-top[3]);return [0,1,2].map(i=>(top[i]*top[3]+bottom[i]*bottom[3]*(1-top[3]))/(a||1)).concat(a) as Color;}
  function background(el:Element|null):Color|null{if(!el)return [255,255,255,1];const style=getComputedStyle(el);if(style.backgroundImage!=='none')return null;const own=color(style.backgroundColor);if(own[3]===1)return own;const parent=background(el.parentElement);return parent?blend(own,parent):null;}
  function luminance(rgb:Color){return rgb.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);}
  const small:string[]=[],contrast:string[]=[],clipped:string[]=[];
  for(const el of document.querySelectorAll<HTMLElement>('body *')){
   const style=getComputedStyle(el);
   if(!el.getClientRects().length||style.visibility==='hidden'||style.opacity==='0'||el.closest('[hidden],[aria-hidden="true"],button:disabled,fieldset:disabled'))continue;
   const text=[...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent?.trim()).filter(Boolean).join(' ');
   const font=parseFloat(style.fontSize);
   if(text&&font<12)small.push(`${el.tagName}.${el.className} ${font}px`);
   if(el.matches('input:not([type=checkbox]):not([type=radio]),textarea,select')&&font<16)small.push(`${el.tagName}.${el.className} control ${font}px`);
   if(text){const bg=background(el);if(bg){const fg=blend(color(style.color),bg);const a=luminance(fg),b=luminance(bg);const ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);const target=font>=24||font>=18.66&&parseInt(style.fontWeight)>=700?3:4.5;if(ratio+0.05<target)contrast.push(`${el.tagName}.${el.className} ${ratio.toFixed(2)}: ${text.slice(0,65)}`);}}
   if(el.matches('button')&&el.clientWidth&&el.scrollWidth>el.clientWidth+2)clipped.push(`${el.textContent?.trim()} ${el.clientWidth}/${el.scrollWidth}`);
  }
  return {small,contrast,clipped,overflow:document.documentElement.scrollWidth>innerWidth+1};
 });
 await page.screenshot({path:info.outputPath(name+'.png'),scale:'css'});
 expect.soft(issues.small,name+' font sizes').toEqual([]);
 expect.soft(issues.contrast,name+' text contrast (solid surfaces)').toEqual([]);
 expect.soft(issues.clipped,name+' clipped buttons').toEqual([]);
 expect.soft(issues.overflow,name+' horizontal overflow').toBe(false);
}
