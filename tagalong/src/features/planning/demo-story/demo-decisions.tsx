'use client';
import type {Plan} from '@/services/types';
import type {DemoChoice,DemoStory,DemoVoteRound} from '@/services/demo-plan';
import {publicWebUrl} from '@/services/place-links';
import {Button} from '@/components/ui/button';
import {useDemoStory} from './use-demo-story';
import {StoryPhoto} from './source-photo';
import './demo-decisions.css';

export function DemoDecisions({plan,compact=false}:{plan:Plan;compact?:boolean}){
 const {story,loading,error,reload}=useDemoStory(plan);
 if(plan.demo_template!=='austin-four-friends')return null;
 return <section className={'demo-decisions'+(compact?' demo-decisions-compact':'')} aria-label="Four friends’ planning decisions" aria-busy={loading}>
  <header className="demo-decisions-heading"><div><span className="eyebrow">FOUR FRIENDS, ONE SHARED PLAN</span><h2>From different ideas to a weekend together.</h2><p>Inspect the options, the first disagreements and the four friends’ final responses.</p></div><span className="status">Fictional group agreement</span></header>
  <p className="demo-decisions-disclosure">Fictional friends · scripted AI and votes · nothing booked. These responses belong to the demonstration and are separate from actual account members and live decision ballots.</p>
  {loading&&<p role="status">Loading the friends’ decisions…</p>}{error&&<div><p role="alert">{error}</p><Button variant="outline" onClick={reload}>Reload demo decisions</Button></div>}
  {story&&<><div className="demo-decision-cast" aria-label="Fictional group">{story.cast.map(person=><span key={person.name}><i style={{backgroundColor:person.color}} aria-hidden="true">{person.name[0]}</i>{person.name}</span>)}</div>
   <div className="demo-agreement-summary"><strong>{story.choices.length} shared selections</strong><span>Destination, dates, lodging, restaurant and activity</span><small>Story agreement only · verify arrangements before booking</small></div>
   <div className="demo-decision-grid">{story.choices.map(choice=><ChoiceCard key={choice.category} choice={choice} story={story} compact={compact}/>)}</div>
  </>}
 </section>;
}

function ChoiceCard({choice,story,compact}:{choice:DemoChoice;story:DemoStory;compact:boolean}){
 const rounds=choice.rounds?.length?choice.rounds:[{title:'Final fictional responses',option:choice.label,votes:choice.votes||{},sourceIds:choice.sourceIds}];
 const initial=rounds.length>1?rounds[0]:null;
 const final=rounds[rounds.length-1];
 const content=<><h4>Options considered</h4><ul className="demo-considered-options">{choice.alternatives?.map(alternative=><li key={alternative}>{alternative}</li>)}</ul>
  {initial&&<VoteRound round={initial} story={story} initial/>}
  <aside className="demo-ai-resolution"><span className="eyebrow">HOW THE GROUP MOVED FORWARD</span><h4>Scripted AI helped connect the needs</h4><p>{initial?.resolution||choice.reason}</p><Evidence story={story} sourceIds={initial?.sourceIds||choice.sourceIds||[]}/></aside>
  <VoteRound round={final} story={story}/>
  <h4>Why this choice?</h4><p>{choice.reason}</p><Evidence story={story} sourceIds={choice.sourceIds||[]}/>
 </>;
 return <article className="demo-decision-card" aria-label={choice.category+' demo decision'}>
  {choice.image&&<StoryPhoto image={choice.image} label={choice.label}/>}
  <div className="demo-decision-body"><div className="demo-decision-title"><span className="eyebrow">{choice.category}</span><small>4 friends · shared selection</small></div><h3>{choice.label}</h3>
   {publicWebUrl(choice.url)&&<a href={publicWebUrl(choice.url)} target="_blank" rel="noopener noreferrer">Official reference website</a>}
   {choice.estimate!=null&&<p className="demo-cost-estimate">Fictional estimate USD {choice.estimate} per person · verify actual prices</p>}
   {compact?<details><summary>Inspect options and votes for {choice.category.toLowerCase()}</summary>{content}</details>:content}
   <p className="demo-not-booked">Not booked · provider details need verification</p>
  </div>
 </article>;
}

function VoteRound({round,story,initial=false}:{round:DemoVoteRound;story:DemoStory;initial?:boolean}){
 return <section className={'demo-vote-round'+(initial?' initial-round':'')} aria-label={round.title}><h4>{round.title}</h4><p>{round.option}</p><table><caption>{initial?'First responses · disagreement remains':'Final responses · fictional agreement'}</caption><thead><tr><th scope="col">Friend</th><th scope="col">Response</th></tr></thead><tbody>{story.cast.map(person=><tr key={person.name}><th scope="row"><span className="demo-voter"><i style={{backgroundColor:person.color}} aria-hidden="true">{person.name[0]}</i>{person.name}</span></th><td><span className={'demo-response '+(round.votes[person.name]||'').split(':')[0].replaceAll(' ','_')}>{responseLabel(round.votes[person.name])}</span></td></tr>)}</tbody></table></section>;
}
function responseLabel(value:string|undefined){if(!value)return 'Not recorded in saved story';return value.replaceAll('can_live_with','Can live with').replace(/^support\b/i,'Support').replace(/^object\b/i,'Object');}
function Evidence({story,sourceIds}:{story:DemoStory;sourceIds:string[]}){
 return <details className="demo-choice-evidence"><summary>Saved evidence ({sourceIds.length})</summary>{sourceIds.map(id=>{const source=story.sources.find(item=>item.id===id);return source?<blockquote key={id}><strong>{source.title}</strong><small>Source ID: {source.id}</small><p>{source.text}</p></blockquote>:<p key={id}>Source {id} is unavailable.</p>;})}<small>Scripted explanation of saved evidence. Live AI responses and citations appear separately in Chat.</small></details>;
}
