'use client';
import { CheckCheck, FileText, GitBranch, ShieldCheck } from 'lucide-react';
import { CouncilView } from './council';
import { currency } from '../lib/format';
import type { Answer, Scenario } from '../lib/types';
import { Badge, Status } from './ui';

export function ScenarioView({scenarios}:{scenarios:Scenario[]}) {
 return <div className="scenario-results"><div className="scenario-grid">{scenarios.map((s,i)=><article className={`scenario-card ${s.passed?'passes':'fails'}`} key={i}>
  <div className="row"><span className="eyebrow">Option {i+1}</span><Badge tone={s.passed?'green':'amber'}>{s.passed?'Constraints met':'Constraint warning'}</Badge></div>
  <h3>{s.name||'Your scenario'}</h3>
  {s.loan&&<p className="muted">{currency(s.loan.principal)} financed · {s.loan.apr}% APR · {s.loan.months} months</p>}
  <dl className="scenario-figures"><div><dt>Monthly surplus</dt><dd>{currency(s.result.monthly_surplus,true)}</dd></div><div><dt>Cash remaining</dt><dd>{currency(s.result.remaining_cash)}</dd></div><div><dt>House savings remaining</dt><dd>{currency(s.result.house_savings)}</dd></div><div><dt>House goal timeline</dt><dd>{s.goal_impact.projected_months===null?'Not reachable':`${s.goal_impact.projected_months} months`}</dd></div><div><dt>Delay vs. baseline</dt><dd>{s.goal_impact.delay_months===null?'Undefined':`+${s.goal_impact.delay_months} months`}</dd></div></dl>
  <div className="constraint-list">{Object.entries(s.constraints).map(([name,c])=><div key={name}><Status passed={c.passed}>{name.replaceAll('_',' ')}</Status></div>)}</div>
  <details><summary>Calculation steps</summary><div className="calculation-list">{s.calculation_steps.map(step=><div key={step.name}><strong>{step.name}</strong><code>{step.expression}</code><span>= {currency(step.value,true)}</span></div>)}</div><p className="muted">Baseline surplus: {currency(String(s.baseline.monthly_surplus))}. Baseline house timeline: {String(s.baseline.house_months)} months. Goal savings are part of total cash.</p></details>
 </article>)}</div>{scenarios[0]&&<details className="assumptions"><summary>Projection assumptions & limitations</summary><ul>{scenarios[0].assumptions.map((x,i)=><li key={i}>{x}</li>)}</ul></details>}</div>;
}

export function AnswerView({answer}:{answer:Answer}) {
 return <article className="answer-card"><div className="row wrap"><span className="answer-brand"><ShieldCheck size={19}/> FinPilot analysis</span><Badge tone={answer.completeness==='complete evidence'?'green':'amber'}>{answer.completeness}</Badge></div>
  <p className="answer-summary">{answer.summary}</p>
  <CouncilView council={answer.council} facts={answer.facts} scenarios={answer.scenarios}/>
  {answer.facts.length>0&&<div className="fact-grid">{answer.facts.map((f,i)=><div key={i}><span>{f.label}</span><strong>{f.value===null?'No matching data':f.unit==='USD'?currency(f.value,true):`${f.value}${f.unit==='percent'?'%':` ${f.unit}`}`}</strong><small>Source: {f.source.replaceAll('_',' ')}</small></div>)}</div>}
  {answer.data_period&&<p className="fine">Period: {answer.data_period.start} through {answer.data_period.end_exclusive} (end excluded).</p>}
  {answer.items&&answer.items.length>0&&<div className="simple-list">{answer.items.map((r,i)=><div className="row" key={i}><span>{r.merchant_normalized||r.merchant||r.category}</span><strong>{currency(r.monthly_equivalent||r.amount,true)}</strong></div>)}</div>}
  {answer.scenarios.length>0&&<ScenarioView scenarios={answer.scenarios}/>}
  <div className="answer-drawers"><details><summary><FileText size={16}/>Evidence & sources <Badge>{answer.sources.length}</Badge></summary>{answer.sources.length?answer.sources.map(s=><blockquote className="source" key={s.chunk_id}><div className="row"><strong>{s.title}</strong><Badge>v{s.version}</Badge></div><small>Page {s.page} · {s.section}{s.superseded?' · superseded':''}</small><p>{s.passage}</p></blockquote>):<p className="muted">{answer.route==='sql'?'This answer uses transaction SQL; no document retrieval was needed.':'This answer uses structured records or requires more evidence.'}</p>}
  {answer.calculation&&<div className="source"><h4>Calculation definition</h4><p>{answer.calculation.calculation_definition}</p>{answer.calculation.exclusion_rules&&<p className="fine">Excluded: {answer.calculation.exclusion_rules.join(', ')}.</p>}</div>}</details>
  <details><summary><GitBranch size={16}/>Agent & tool trace <Badge>{answer.tools.length} tools</Badge></summary><p className="fine">{answer.mode} · {answer.latency_ms} ms · {answer.tracing}</p><ol className="trace">{answer.events.map((e,i)=><li key={i}><span className={`trace-dot ${e.status==='blocked'?'blocked':''}`}/><div><strong>{e.node}</strong><code>{e.tool}</code><small>{e.summary} · {e.latency_ms} ms</small></div><Badge tone={e.status==='blocked'?'red':'green'}>{e.status}</Badge></li>)}</ol></details>
  <details><summary><CheckCheck size={16}/>Validation & limitations</summary><Status passed={answer.validation.passed}>{answer.validation.passed?'Deterministic checks passed':'Answer blocked or incomplete'}</Status><ul>{[...answer.validation.checks,...answer.validation.errors,...answer.limitations].map((s,i)=><li key={i}>{s}</li>)}</ul><p className="fine">Validation checks provenance and calculation identities. It is not a guarantee of financial suitability.</p></details></div>
 </article>;
}
