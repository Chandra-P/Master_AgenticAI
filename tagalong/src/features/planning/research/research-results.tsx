'use client';
import Image from 'next/image';
import {Button} from '@/components/ui/button';
import {publicWebUrl,safeActivityImage} from '@/services/place-links';
import type {ResearchResult,ResearchOption} from '@/services/option-research';

/** Presentation only: request scope and save behavior remain in OptionWorkbench. */
export function ResearchResults({result,disabled,onFit,onChoose}:{result:ResearchResult;disabled:boolean;onFit:(option:ResearchOption)=>void;onChoose:(option:ResearchOption)=>void}){
 return <>
    <section className="research-receipt" aria-label="Sources and tools used"><h3>What Tagalong actually used</h3><ol>{result.steps.map(step=><li key={step.id}><strong>{step.label}</strong> · {step.status}<p>{step.detail}</p></li>)}</ol></section>
    <section aria-label="Remembered group context"><h3>From your group</h3><p>Compare these saved facts with the options below. Search results do not establish suitability or consensus.</p>{result.sources.filter(source=>!source.id.startsWith('external:')).map(source=><details key={source.id}><summary>{source.title}</summary><p className="research-source">{source.id==='plan-facts'?readableFacts(source.text):source.text}</p></details>)}{!result.sources.some(source=>source.id!=='plan-facts'&&!source.id.startsWith('external:'))&&<p>No saved evidence was found. Add preferences in Chat or Notes before assessing group fit.</p>}{result.context_truncated&&<p>Only selected evidence excerpts were reviewed.</p>}</section>
    <div className="research-options">{result.options.map(option=><article key={option.id}>
     {safeActivityImage(option.image)?<Image src={safeActivityImage(option.image)!} alt={'Image from the source for '+option.name} unoptimized width={360} height={180} referrerPolicy="no-referrer"/>:<div className="research-no-image">No verified source image available</div>}
     <h3>{option.name}</h3><p>{option.details}</p><small>External search information · verify details with the venue.</small>
     {publicWebUrl(option.url)&&<a href={publicWebUrl(option.url)} target="_blank" rel="noopener noreferrer">Explore {option.name}</a>}
     <div className="option-actions"><Button variant="outline" onClick={()=>onFit(option)}>Does it fit our group?</Button><Button disabled={disabled} onClick={()=>onChoose(option)}>Review and add option</Button></div>
    </article>)}</div>{!result.options.length&&<p>No place options were returned. Refine your query or add a place manually.</p>}
 </>;
}

function readableFacts(text:string){try{const facts=JSON.parse(text);return [`Plan: ${facts.title}`,`Location: ${facts.location}`,`Dates: ${facts.start||'not set'} to ${facts.end||'not set'}`,`Working budget per person: ${facts.budget>0?facts.budget:'not set'}`,`Confirmed preferences: ${(facts.confirmed_preferences||[]).join(', ')||'none recorded'}`].join('\n');}catch{return text;}}
