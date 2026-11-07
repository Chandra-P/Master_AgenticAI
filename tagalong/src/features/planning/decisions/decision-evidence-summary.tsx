'use client';
import {useEffect,useRef,useState} from 'react';
import {Button} from '@/components/ui/button';
import type {DecisionSummary} from '@/services/decisions';
export function DecisionEvidenceSummary({decisionId,decisionVersion,planRevision,identity,connected,summarize,onComments,commentCount}:{decisionId:string;decisionVersion:number;planRevision:number;identity:string;connected:boolean;summarize:(id:string)=>Promise<DecisionSummary>;onComments:()=>void;commentCount:number}){
 const key=[identity,decisionId,decisionVersion,planRevision].join('|');
 const [cached,setCached]=useState<{key:string;summary:DecisionSummary}|null>(null);
 const [pendingKey,setPendingKey]=useState('');const [failure,setFailure]=useState<{key:string;text:string}|null>(null);
 const currentKey=useRef(key);const inFlight=useRef(false);
 useEffect(()=>{currentKey.current=key;return()=>{currentKey.current='';};},[key]);
 const summary=cached?.key===key&&cached.summary.decisionId===decisionId&&cached.summary.decisionVersion===decisionVersion&&cached.summary.planRevision===planRevision?cached.summary:null;
 const live=connected&&summary?.providerStatus==='live';
 async function request(){
  if(inFlight.current)return;
  const requestedKey=key;inFlight.current=true;setPendingKey(requestedKey);setFailure(null);
  try{const result=await summarize(decisionId);if(currentKey.current===requestedKey)setCached({key:requestedKey,summary:result});}
  catch{if(currentKey.current===requestedKey)setFailure({key:requestedKey,text:'Decision summary could not be generated. Current recorded evidence remains available.'});}
  finally{inFlight.current=false;if(currentKey.current===requestedKey)setPendingKey('');}
 }
 return <section className="decision-evidence" aria-label="Decision summary"><h4>{live?'AI decision summary':'Decision summary'}</h4>{live?<><p>{summary.text}</p><small>Generated {summary.generatedAt?new Date(summary.generatedAt).toLocaleString():'time unavailable'} · decision version {summary.decisionVersion} · plan revision {summary.planRevision}</small><details><summary>Evidence used ({summary.sources.length})</summary>{summary.sources.map(source=><div key={source.id} id={'evidence-'+source.id}><strong>{source.title}</strong><small> · source version {source.version}</small><p>{source.text}</p></div>)}</details></>:<p>{summary?.providerStatus==='unavailable'?'AI summary unavailable. ':''}Summary not available. Current responses above are the recorded evidence.</p>}{failure?.key===key&&<p role="alert">{failure.text}</p>}<p><a href={'#decision-'+decisionId}>View current-version responses</a>{commentCount>0&&<> · <a href={'#comments-'+decisionId} onClick={onComments}>View decision comments</a></>}</p>{connected&&<Button variant="outline" disabled={pendingKey===key} onClick={()=>void request()}>{pendingKey===key?'Summarizing decision…':'Summarize decision'}</Button>}</section>;
}
