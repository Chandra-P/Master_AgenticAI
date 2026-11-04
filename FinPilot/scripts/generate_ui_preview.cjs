// Render the actual React dashboard with synthetic API fixtures, without a server.
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const frontend=path.join(root,'frontend');
const esbuild=require(path.join(frontend,'node_modules/esbuild'));
const out=path.join(root,'artifacts/ui-preview');
fs.mkdirSync(out,{recursive:true});
const councilDemo=JSON.parse(fs.readFileSync(path.join(root,'artifacts/council-demo.json'),'utf8'));
const data=JSON.parse(fs.readFileSync(path.join(root,'artifacts/ui-preview-data.json'),'utf8'));
(async()=>{
 const bundle=path.join(out,'.render.cjs');
 await esbuild.build({stdin:{contents:`import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';import Home from './app/page';import {AnswerView} from './components/evidence';export function render(){return renderToStaticMarkup(<Home/>);}export function renderAnswer(answer){return renderToStaticMarkup(<AnswerView answer={answer}/>);}`,resolveDir:frontend,loader:'tsx'},bundle:true,platform:'node',format:'cjs',outfile:bundle,jsx:'automatic',plugins:[{name:'synthetic-preview',setup(build){
  build.onResolve({filter:/lib\/api$/},()=>({path:'api',namespace:'preview'}));
  build.onLoad({filter:/.*/,namespace:'preview'},()=>({contents:`const fixtures=${JSON.stringify(data)};export function useResource(path){return {data:fixtures[path]||null,loading:false,error:null,refresh:()=>{},setData:()=>{}};}export async function api(){throw new Error('Static preview: launch the app to use controls.');}`,loader:'js',resolveDir:frontend}));
  build.onResolve({filter:/^recharts$/},()=>({path:'charts',namespace:'charts'}));
  build.onResolve({filter:/^real-charts$/},()=>({path:path.join(frontend,'node_modules/recharts/lib/index.js')}));
  build.onLoad({filter:/.*/,namespace:'charts'},()=>({contents:`import React from '${path.join(frontend,'node_modules/react/index.js')}';export * from 'real-charts';export function ResponsiveContainer({children}){return React.cloneElement(children,{width:720,height:260});}`,loader:'js',resolveDir:frontend}));
 }}]});
 const renderer=require(bundle);const content=renderer.render();
 const css=['globals.css','modern.css'].map(p=>fs.readFileSync(path.join(frontend,'app',p),'utf8')).join('\n');
 for(const view of ['overview','council'])for(const theme of ['light','dark']){
  const viewContent=view==='council'?content.replace(/<main\b[^>]*>[\s\S]*?<\/main>/,`<main id="main-content" class="main-content"><div class="page-heading"><div><div class="eyebrow">SYNTHETIC DEMONSTRATION</div><h1>Three reviews. One grounded decision.</h1><p>Actual React answer panel · simulated council votes.</p></div></div>${renderer.renderAnswer(councilDemo)}</main>`):content;
  const inactive=viewContent.replace(/<(button|input|select|textarea)\b/g,'<$1 disabled');
  const html=`<!doctype html><html lang="en" data-theme="${theme}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>FinPilot · Static React preview</title><style>${css}\n.preview-banner{position:fixed;inset:0 0 auto;z-index:500;height:44px;background:#e0f2fe;color:#0c4a6e;display:flex;align-items:center;justify-content:center;gap:16px;font:12px system-ui}.preview-banner a{color:inherit;text-decoration:underline}body{padding-top:44px}.sidebar{top:44px}.topbar{top:44px}button:disabled,input:disabled,select:disabled{opacity:1!important;cursor:default!important}</style></head><body><div class="preview-banner">Static React preview · synthetic data · controls inactive <a href="index.html">Light</a><a href="dark.html">Dark</a><a href="council.html">Council</a></div>${inactive}</body></html>`;
  fs.writeFileSync(path.join(out,view==='council'?(theme==='light'?'council.html':'council-dark.html'):(theme==='light'?'index.html':'dark.html')),html);
 }
 fs.unlinkSync(bundle);
 console.log('Generated dashboard and council light/dark static previews from actual React components.');
})().catch(e=>{console.error(e);process.exitCode=1});
