'use client';
import {useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {Button} from '@/components/ui/button';
import {Dialog} from '@/components/ui/dialog';
import {publicWebUrl} from '@/services/place-links';
import type {DemoStory} from '@/services/demo-plan';
import {usePlanning} from '../store';
import {StoryPhoto} from './source-photo';
import './austin-demo-preview.css';

type PublicStory=DemoStory&{messages:{id:string;author:string;text:string;time:string;assistant:boolean;simulation:boolean;sources?:{id:string;title:string;text:string}[]}[]};

export function AustinDemoPreview(){
 const router=useRouter();const {setMode}=usePlanning();
 const [open,setOpen]=useState(false),[story,setStory]=useState<PublicStory|null>(null),[step,setStep]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function show(){
  setOpen(true);setError('');setStep(0);if(story)return;
  setBusy(true);
  try{const response=await fetch('/api/backend/v1/public/demo-stories/austin-four-friends',{cache:'force-cache'});const data=await response.json();if(!response.ok)throw new Error(typeof data?.detail==='string'?data.detail:'The Austin story is temporarily unavailable.');setStory(data as PublicStory);}
  catch(cause){setError(cause instanceof Error?cause.message:'The Austin story is temporarily unavailable.');}
  finally{setBusy(false);}
 }
 const milestone=story?.milestones[step];
 const scene=story?.messages.filter(message=>message.time.startsWith('Scene '+(step+1)+' ·'))||[];
 return <>
  <Button type="button" variant="outline" className="austin-demo-launch" onClick={()=>void show()}>See four friends plan an Austin weekend <span aria-hidden="true">→</span></Button>
  <Dialog open={open} onOpenChange={setOpen} title="Four friends, one Austin weekend" description="A guided, fictional walkthrough from first idea to shared itinerary.">
   <div className="austin-demo-preview" aria-busy={busy}>
    <p className="austin-demo-disclosure"><strong>Fictional demo:</strong> Alex, Maya, Sam and Jordan, their conversation and votes are scripted. This replay shows saved example evidence; it does not run a live model or retrieval request. Nothing is booked.</p>
    {busy&&<p role="status">Loading the Austin story…</p>}{error&&<p role="alert">{error}</p>}
    {story&&<>
     <nav className="austin-demo-progress" aria-label="Austin trip story steps">{story.milestones.map((item,index)=><button type="button" aria-current={index===step?'step':undefined} key={item.id} onClick={()=>setStep(index)}>{index+1}. {item.title.replace(/^\d+\.\s*/,'')}</button>)}</nav>
     {milestone&&<section className="austin-demo-scene" aria-live="polite"><div className="eyebrow">STEP {step+1} OF {story.milestones.length}</div><h3>{milestone.title.replace(/^\d+\.\s*/,'')}</h3><p>{milestone.text}</p>{milestone.ai&&<strong className="austin-demo-ai-label">Scripted AI · saved evidence illustration</strong>}
      {scene.map(message=><article key={message.id} className={message.assistant?'austin-demo-message austin-demo-assistant':'austin-demo-message'}><strong>{message.author}{message.assistant?' · Scripted AI':''}</strong><p>{message.text}</p>{message.sources&&message.sources.length>0&&<details><summary>Evidence shown in this scripted reply ({message.sources.length})</summary>{message.sources.map(source=><blockquote key={source.id}><strong>{source.title}</strong><small>Saved source ID: {source.id}</small><p>{source.text}</p></blockquote>)}</details>}</article>)}
      <div className="austin-demo-step-actions"><Button type="button" variant="outline" disabled={step===0} onClick={()=>setStep(current=>Math.max(0,current-1))}>Previous</Button><Button type="button" disabled={step>=story.milestones.length-1} onClick={()=>setStep(current=>Math.min(story.milestones.length-1,current+1))}>{step===story.milestones.length-1?'End of story':'Next step'}</Button></div>
     </section>}
     <section><h3>Options, objections, and votes</h3><p className="muted">Open a decision to see what they considered and how the fictional group changed its response.</p><div className="austin-demo-options">{story.choices.map(choice=><details className="austin-demo-option" key={choice.category}><summary><span><small>{choice.category}</small><strong>{choice.label}</strong></span><span>Inspect options and votes</span></summary>{choice.image&&<StoryPhoto image={choice.image} label={choice.label}/>}<p>{choice.reason}</p>{publicWebUrl(choice.url)&&<a href={publicWebUrl(choice.url)} target="_blank" rel="noopener noreferrer">Official reference website ↗</a>}{choice.estimate!==null&&<p>Fictional estimate: ${choice.estimate} per person. Verify actual prices and availability.</p>}<h4>Alternatives discussed</h4><ul>{choice.alternatives?.map(option=><li key={option}>{option}</li>)}</ul>{choice.rounds?.map(round=><section className="austin-demo-vote-round" key={round.title}><h4>{round.title}: {round.option}</h4><ul>{Object.entries(round.votes).map(([person,vote])=><li key={person}><strong>{person}:</strong> {vote.replaceAll('_',' ')}</li>)}</ul></section>)}<details><summary>Group evidence used in the story</summary>{choice.sourceIds?.map(id=>{const source=story.sources.find(item=>item.id===id);return source?<blockquote key={id}><strong>{source.title}</strong><p>{source.text}</p></blockquote>:null;})}</details></details>)}</div></section>
     <section><h3>Final three-day itinerary</h3><p className="muted">The friends agree on a shared outline; all venue costs and details remain fictional or unverified.</p>{story.days.map(day=><article className="austin-demo-day" key={day.date}><div><h4>{day.title}</h4><small>{day.date}</small></div><ol>{day.items.map(item=><li key={item.time+item.title}><StoryPhoto image={item.image} label={item.location}/><div><strong>{item.time} · {item.title}</strong><span>{item.location}</span><small>Draft idea · not booked</small></div></li>)}</ol></article>)}</section>
     <aside className="austin-demo-live"><h3>Show live RAG and AI</h3><p>Sign in, open the saved Austin demo plan, and choose <strong>Run live RAG and AI check</strong>. That connected flow sends the fictional plan context to your configured providers and displays the actual reply with citations in Chat. It uses provider quota.</p><Link className="btn btn-outline" href="/account" onClick={event=>{event.preventDefault();setOpen(false);setMode('connected');router.push('/account');}}>Sign in to run the live check</Link></aside>
    </>}
   </div>
  </Dialog>
 </>;
}
