import {useEffect,useRef,useState} from 'react';
import './plan.css';

type Vendor={id:string;name:string;address?:string;directory_version:number;price:number|null;price_type:string;capacity:number|null;checked_on:string;source_url:string;contact?:{phone_e164:string;phone_display:string;organization:string;contact_url:string}};
type Option={vendor:Vendor;status:string;reasons:string[];missing:string[];conditions:string[];exclusion_reasons:string[]};
type Group={options:Option[];conditional:Option[];excluded:Option[]};
type Plan={brief_version:number;run_id:string;groups:Record<string,Group>;completed_nodes:string[];known_minimum_combination:number|null;cost_note:string;budget_status:string;gaps:string[];guests:number};
type Shortlist={selected:Vendor[];stale:{vendor_id:string;reason:string}[]};
type Draft={group_id:string;vendor_ids:string[];to:string[];subject:string;body:string;status:string;missing:string[]};
type Event={id:string;confirmed_version:number|null;brief:{version:number}};
type Api=(path:string,body?:unknown)=>Promise<any>;

export function ApprovedPlan({event,locked,api}:{event:Event|null;locked:boolean;api:Api}){
  const [plan,setPlan]=useState<Plan|null>(null),[shortlist,setShortlist]=useState<Shortlist>({selected:[],stale:[]});
  const [drafts,setDrafts]=useState<Draft[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [category,setCategory]=useState('venue');
  const generation=useRef(0);
  const confirmed=!!event&&event.confirmed_version===event.brief.version;
  const key=event?`${event.id}:${event.brief.version}:${event.confirmed_version}`:'';
  const currentKey=useRef(key);currentKey.current=key;
  async function load(){
    if(!event||!confirmed)return;
    const ticket=++generation.current,captured=key,path=`/api/events/${event.id}`;
    setBusy(true);setError('');setPlan(null);setDrafts([]);setShortlist({selected:[],stale:[]});
    try{
      const [result,saved]=await Promise.all([api(path+'/recommendations',{expected_version:event.brief.version}),api(path+`/shortlist?expected_version=${event.brief.version}`)]);
      const prepared=await api(path+'/drafts',{expected_version:event.brief.version});
      if(ticket!==generation.current||captured!==currentKey.current)return;
      setPlan(result);setCategory(Object.keys(result.groups)[0]);setShortlist(saved);setDrafts(prepared.drafts);
    }catch(e){if(ticket===generation.current&&captured===currentKey.current)setError((e as Error).message);}
    finally{if(ticket===generation.current&&captured===currentKey.current)setBusy(false);}
  }
  useEffect(()=>{generation.current++;setPlan(null);setDrafts([]);setShortlist({selected:[],stale:[]});setError('');setBusy(false);if(confirmed)void load();
    return()=>{generation.current++;};},[key]);
  async function select(vendor:Vendor){
    if(!event||busy||locked)return;
    const captured=key,ticket=++generation.current;setBusy(true);setError('');setDrafts([]);
    try{
      const saved=await api(`/api/events/${event.id}/shortlist`,{expected_version:event.brief.version,
        vendor_id:vendor.id,vendor_version:vendor.directory_version,selected:!shortlist.selected.some(v=>v.id===vendor.id)});
      const prepared=await api(`/api/events/${event.id}/drafts`,{expected_version:event.brief.version});
      if(ticket===generation.current&&captured===currentKey.current){setShortlist(saved);setDrafts(prepared.drafts);}
    }catch(e){if(ticket===generation.current&&captured===currentKey.current){setPlan(null);setShortlist({selected:[],stale:[]});setError((e as Error).message);}}
    finally{if(ticket===generation.current&&captured===currentKey.current)setBusy(false);}
  }
  if(!confirmed)return null;
  const group=plan?.groups[category];
  function card(option:Option){const v=option.vendor,chosen=shortlist.selected.some(item=>item.id===v.id);
    return <article className="vendor-card" key={v.id}><span className="vendor-status">{option.status==='conditional'?'More facts needed':'Candidate · needs quotes'}</span><h3>{v.name}</h3><p>{v.address}</p><div className="vendor-facts"><span>{v.price==null?'Published price unknown':`$${v.price.toLocaleString()} ${v.price_type==='published_base'?'published base':'starting/minimum'}`}</span><small>Rate snapshot {v.checked_on} · directory v{v.directory_version}</small></div><ul className="fit-reasons">{option.reasons.map(x=><li key={x}>{x}</li>)}{option.conditions.map(x=><li key={x}>{x}</li>)}</ul><details className="option-gaps"><summary>What needs confirmation?</summary><ul>{option.missing.map(x=><li key={x}>{x}</li>)}</ul></details>
      {v.contact&&<p className="plan-contact">{v.contact.organization}<br/>{/^\+[1-9]\d{7,14}$/.test(v.contact.phone_e164)&&<a href={`tel:${v.contact.phone_e164}`}>{v.contact.phone_display}</a>} · <a href={v.contact.contact_url} target="_blank" rel="noopener noreferrer">Contact page</a></p>}
      <div className="option-actions"><button disabled={busy||locked} onClick={()=>void select(v)}>{chosen?'Remove from shortlist':'Shortlist this option'}</button><a href={v.source_url} target="_blank" rel="noopener noreferrer">Official source ↗</a></div></article>;
  }
  return <section className="approved-plan" aria-label="Your approved vendor options"><div className="directory-heading"><div><p className="eyebrow">YOUR BRIEF, MATCHED TO APPROVED PROVIDERS</p><h2>Options for your celebration</h2><p>All {plan?.guests??'invited'} guests included. Published costs are starting points; availability and complete quotes need confirmation.</p></div><button className="directory-toggle" disabled={busy||locked} onClick={()=>void load()}>Refresh approved options ↻</button></div>
    {error&&<p className="alert" role="alert">{error} Refresh to compare the current approved list.</p>}{busy&&<p role="status">{plan?'Updating your shortlist and preparing drafts…':'Comparing your confirmed brief with the approved directory…'}</p>}
    {plan&&<><div className="workflow-proof"><span>Completed catalog workflow:</span>{plan.completed_nodes.map(node=><span key={node}>✓ {node}</span>)}</div><p className="plan-cost"><strong>{plan.known_minimum_combination==null?'Some selected services have no comparable published price':`From $${plan.known_minimum_combination.toLocaleString()} in known base/minimum costs for one option per selected service`}</strong><br/>{plan.cost_note}</p>{plan.budget_status==='needs_changes'&&<p className="alert">The approved list cannot currently meet every constraint. Your budget and guest count have not been changed; choose which priority to revisit.</p>}
      <div className="directory-controls"><label htmlFor="plan-category">Compare</label><select id="plan-category" value={category} onChange={e=>setCategory(e.target.value)}>{Object.keys(plan.groups).map(k=><option key={k} value={k}>{k==='decoration'?'Professional decorations':k==='food'?'Food providers':'Venues'}</option>)}</select><span>No web search · No messages sent</span></div><div className="vendor-grid">{group?.options.map(card)}</div>
      {!!group?.conditional.length&&<><h3 className="subheading">Options needing more facts before a fit can be assessed</h3><div className="vendor-grid">{group.conditional.map(card)}</div></>}
      {!group?.options.length&&!group?.conditional.length&&<p className="directory-empty">No approved options meet the known requirements in this category. We won’t fill the list with unapproved vendors.</p>}
      {!!group?.excluded.length&&<details className="excluded-options"><summary>{group.excluded.length} approved options excluded for this brief</summary>{group.excluded.map(o=><p key={o.vendor.id}><strong>{o.vendor.name}</strong>: {o.exclusion_reasons.join(' ')}</p>)}</details>}
      <details className="comparison-gaps"><summary>Coverage and remaining gaps</summary><ul>{plan.gaps.map(g=><li key={g}>{g}</li>)}</ul></details>
      {!!shortlist.stale.length&&<p className="alert">Some shortlisted records changed approval/version. Review them before preparing an inquiry.</p>}
      {!!drafts.length&&<div className="inquiry-previews"><p className="eyebrow">AUTOMATICALLY PREPARED · FOR YOUR REVIEW</p><h3>Your inquiry drafts</h3><p>These are alternatives you shortlisted, not bookings. Shared reservation offices receive one combined draft.</p>{drafts.map(d=><details key={d.group_id} className="inquiry-preview"><summary>{d.subject} · {d.vendor_ids.length} {d.vendor_ids.length===1?'option':'alternatives'}</summary><p><strong>To:</strong> {d.to.join(', ')||'No verified email yet'}</p><pre>{d.body}</pre><ul>{d.missing.map(x=><li key={x}>{x}</li>)}</ul><strong>{d.status}</strong></details>)}</div>}
    </>}
    <p className="plan-footnote">Saved to this browser session. Google sign-in for cross-device access and Gmail sending are still being set up. Nothing here sends an email or secures a reservation.</p>
  </section>;
}
