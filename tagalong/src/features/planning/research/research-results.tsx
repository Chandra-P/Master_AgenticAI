'use client';
import Image from 'next/image';
import type {MouseEvent} from 'react';
import {Button} from '@/components/ui/button';
import {publicWebUrl,safeActivityImage} from '@/services/place-links';
import type {ResearchResult,ResearchOption,ResearchFinding} from '@/services/option-research';

/** A compact view of the agent's real search → retrieval → assessment run. */
export function ResearchResults({result,disabled,onFit,onChoose}:{result:ResearchResult;disabled:boolean;onFit:(option:ResearchOption)=>void;onChoose:(option:ResearchOption)=>void}){
 const groupSources=result.sources.filter(source=>!source.id.startsWith('external:'));
 const pineconeSources=groupSources.filter(source=>source.retrieval_origin==='pinecone');
 const stages=[
  {id:'search',title:'Places search tool',value:stepState(result,'search'),detail:stepDetail(result,'search')},
  {id:'retrieval',title:'Pinecone RAG',value:pineconeSources.length?`${pineconeSources.length} group memories found`:stepState(result,'retrieval'),detail:stepDetail(result,'retrieval')},
  {id:'assessment',title:'AI group check',value:result.assessment_status==='available'?`${result.options.length} options compared`:result.assessment_status,detail:stepDetail(result,'assessment')},
 ];
 return <>
  <section className="research-agent-flow" aria-label="AI agent workflow">
   <div className="research-agent-heading"><div><span className="eyebrow">TAGALONG AI AGENT</span><h3>From search to group fit</h3></div><span className="research-agent-tag">Tools + RAG</span></div>
   <ol>{stages.map((stage,index)=><li key={stage.id} data-stage={stage.id}><span className="research-stage-number">{index+1}</span><div><strong>{stage.title}</strong><small>{stage.value}</small></div></li>)}</ol>
   <details className="research-execution-details"><summary>How the agent worked</summary><ol>{result.steps.map(step=><li key={step.id}><strong>{step.label}</strong><span>{step.status.replace('_',' ')}</span><p>{step.detail}</p></li>)}</ol></details>
  </section>
  {result.assessment_status==='available'&&<p className="research-assessment-heading">AI checked these places against your group’s needs.</p>}
  {result.assessment_status==='unavailable'&&<p className="research-assessment-unavailable" role="status">Group-fit check is unavailable. Search results are shown without an AI recommendation.</p>}
  {result.assessment_status==='skipped'&&<p className="research-assessment-unavailable" role="status">No venue options were available to compare.</p>}
  {result.index_freshness.status!=='current'&&<p className="research-freshness" role="status">Older chat memory is {result.index_freshness.status}. Current plan facts and Notes were still checked.</p>}
  <details className="research-group-memory" id="research-group-memory" aria-label="Group memory" role="region">
   <summary><strong>Group memory</strong><span>Pinecone RAG · {pineconeSources.length} retrieved · {groupSources.length} sources</span></summary>
   {result.index_freshness.status!=='current'&&<small>{result.index_freshness.indexed_sources} of {result.index_freshness.current_sources} current sources indexed.</small>}
   {result.context_truncated&&<small>Selected excerpts only.</small>}
   {groupSources.map(source=><details className="research-source-item" id={'research-source-'+source.id} key={source.id}>
    <summary>{source.title}<small>{originLabel(source.retrieval_origin)}</small></summary>
    <p className="research-source">{source.id==='plan-facts'?readableFacts(source.text):source.text}</p>
   </details>)}
   {!groupSources.some(source=>source.id!=='plan-facts')&&<p>No saved group preferences matched. Add preferences in Chat or Notes.</p>}
  </details>
  <div className="research-options">{result.options.map(option=>{
   const assessment=option.assessment;
   const reasonsCount=(assessment?.matches.length||0)+(assessment?.conflicts.length||0)+(assessment?.unknowns.length||0);
   return <article key={option.id}>
    {safeActivityImage(option.image)?<Image src={safeActivityImage(option.image)!} alt={'Image from the source for '+option.name} unoptimized width={360} height={180} referrerPolicy="no-referrer"/>:<div className="research-no-image">No source image</div>}
    <h3>{option.name}</h3><p className="research-option-description">{option.details}</p><small>Public result · verify details with the venue.</small>
    {assessment&&<section className="research-assessment" aria-label={'AI comparison for '+option.name}>
     <div className="research-result-verdict"><span className="eyebrow">TAGALONG CHECK</span><strong data-verdict={assessment.verdict}>{verdictLabel(assessment.verdict)}</strong></div>
     <p className="research-assessment-summary">{assessment.summary}</p>
     <div className="research-result-counts"><span>{assessment.matches.length} matches</span><span>{assessment.conflicts.length} conflicts</span><span>{assessment.unknowns.length} to verify</span></div>
     {reasonsCount>0&&<details className="research-reasons"><summary>Why this result · {reasonsCount} findings</summary>
      {assessment.matches.length>0&&<div><h4>Matches</h4>{findings(assessment.matches,result)}</div>}
      {assessment.conflicts.length>0&&<div><h4>Conflicts</h4>{findings(assessment.conflicts,result)}</div>}
      {assessment.unknowns.length>0&&<div><h4>Still to verify</h4><ul>{assessment.unknowns.map((item,index)=><li key={index}>{item}</li>)}</ul></div>}
     </details>}
    </section>}
    {!assessment&&result.assessment_status==='available'&&<p className="research-assessment-unavailable">No group-fit recommendation. Review this result before proposing it.</p>}
    {publicWebUrl(option.url)&&<a href={publicWebUrl(option.url)} target="_blank" rel="noopener noreferrer">Explore {option.name}</a>}
    <div className="option-actions"><Button variant="outline" onClick={()=>onFit(option)}>Check group fit</Button><Button disabled={disabled} onClick={()=>onChoose(option)}>Add to decision</Button></div>
   </article>;
  })}</div>
  {!result.options.length&&<p>No place options found. Try a venue name or broader search.</p>}
  <section className="research-public-sources" aria-label="Public sources"><details><summary>Public search sources · {result.sources.filter(source=>source.id.startsWith('external:')).length}</summary>{result.sources.filter(source=>source.id.startsWith('external:')).map(source=><details id={'research-source-'+source.id} key={source.id}><summary>{source.title}<small>{originLabel(source.retrieval_origin)}</small></summary><p className="research-source">{source.text}</p></details>)}</details></section>
 </>;
}

function stepState(result:ResearchResult,id:string){const step=result.steps.find(item=>item.id===id);return step?step.status.replace('_',' '):'not run';}
function stepDetail(result:ResearchResult,id:string){return result.steps.find(item=>item.id===id)?.detail||'No execution detail was returned.';}
function findings(items:ResearchFinding[],result:ResearchResult){return <ul>{items.map((item,index)=><li key={index}><p>{item.text}</p><div className="research-citations">{item.source_ids.map(id=>{const sourceIndex=result.sources.findIndex(candidate=>candidate.id===id);const source=result.sources[sourceIndex];return source?<a key={id} href={'#research-source-'+source.id} aria-label={'Evidence '+(sourceIndex+1)+': '+source.title} title={source.title} onClick={event=>showSource(event,source.id)}>Evidence {sourceIndex+1}</a>:null;})}</div></li>)}</ul>;}
function showSource(event:MouseEvent<HTMLAnchorElement>,id:string){if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();const group=document.getElementById('research-group-memory');if(group instanceof HTMLDetailsElement)group.open=true;const source=document.getElementById('research-source-'+id);if(source instanceof HTMLDetailsElement)source.open=true;requestAnimationFrame(()=>source?.scrollIntoView({behavior:'smooth',block:'nearest'}));}
function verdictLabel(verdict:NonNullable<ResearchOption['assessment']>['verdict']){return verdict==='fits'?'Fits group needs':verdict==='conflicts'?'Potential conflict':'More to check';}
function originLabel(origin:string|undefined){switch(origin){case 'pinecone':return 'Pinecone memory';case 'saved_note':return 'Saved note';case 'recent_message':return 'Recent chat';case 'current_decision':return 'Decision comment';case 'postgres':return 'Plan facts';case 'user_input':return 'Your option details';case 'public_search':return 'Search tool';default:return 'Plan evidence';}}
function readableFacts(text:string){try{const facts=JSON.parse(text);return [`Destination: ${facts.location}`,`Dates: ${facts.start||'not set'} – ${facts.end||'not set'}`,`Budget per person: ${facts.budget>0?facts.budget:'not set'}`,`Agreed preferences: ${(facts.confirmed_preferences||[]).join(', ')||'none yet'}`].join('\n');}catch{return text;}}
