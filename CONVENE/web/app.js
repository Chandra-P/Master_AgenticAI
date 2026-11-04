import {budgetSummary, filteredOptions, quoteRequest, researchedOption, readAgentStream, reconcileAgentPrices} from './planner.mjs';

const $ = id => document.getElementById(id);
const money = n => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = value => {try {const url = new URL(value);return ['http:','https:'].includes(url.protocol) ? url.href : '#';}catch{return '#';}};
const STORAGE = 'convene-party-v1';
let catalog, party, selected = {}, quotes = {}, saved = [], extras = [];
let category = 'venues', onlySaved = false;
let toastTimer;
let researchCandidates=[];
let agentController,agentVersion=0,agentResult;

function invalidateAgent(){
  agentVersion++;agentController?.abort();agentResult=null;
  if($('agent-results')){$('agent-results').innerHTML='';$('agent-activity').hidden=true;$('agent-status').textContent='Party details or quotes changed. Run again for updated recommendations.';$('run-agent').disabled=false;}
}

function renderAgentResult(result){
  agentResult=result;
  catalog.venues=reconcileAgentPrices(catalog.venues,result.option_updates||[]);
  catalog.decorators=reconcileAgentPrices(catalog.decorators,result.option_updates||[]);
  renderCards();renderPlan();
  const notes=`<p class="agent-assessment"><strong>${result.mode==='live'?'AI planning assessment':'Catalog-only assessment'}:</strong> ${escape(result.planning_notes)}</p>`;
  const warnings=`<div class="agent-cautions">${result.warnings.map(warning=>`<p>${escape(warning)}</p>`).join('')}</div>`;
  const recommendations=result.recommendations.map((pair,index)=>`<article class="agent-pair"><span class="eyebrow">${index===0?'START HERE':'ANOTHER OPTION'} · NEEDS QUOTES</span><h3>${escape(pair.venue_name)}<span> + </span>${escape(pair.decorator_name)}</h3><p>${escape(pair.reason)}</p><div class="agent-pair-cost"><span><strong>${money(pair.published_subtotal)}</strong> known starting costs / entered quotes</span><span>${money(pair.headroom_after_reserve)} unallocated after your set-aside</span></div><details><summary>What’s still missing?</summary><ul>${pair.missing.map(item=>`<li>${escape(item)}</li>`).join('')}</ul></details><div class="agent-pair-footer"><button class="button button-outline" data-agent-pair="${index}">Use this combination ↗</button><span>Price basis: dated catalog snapshot + any quotes you entered</span></div></article>`).join('');
  const rejected=result.rejected.length?`<details class="agent-rejected"><summary>${result.rejected.length} options ruled out by capacity or budget</summary>${result.rejected.map(item=>`<p><strong>${escape(item.name)}:</strong> ${escape(item.reason)}</p>`).join('')}</details>`:'';
  const leads=result.research_leads?.length?`<details class="agent-leads"><summary>Additional search leads · not verified or included in budget comparisons</summary>${result.research_leads.map(item=>`<p><a target="_blank" rel="noopener noreferrer" href="${escape(safeUrl(item.url))}">${escape(item.title||item.url)} ↗</a></p>`).join('')}</details>`:'';
  const checks=result.source_checks.length?`<details class="agent-source-checks" open><summary>Source check outcomes · ${escape(result.research_status)}</summary>${result.source_checks.map(check=>`<p><strong>${escape(check.status)}:</strong> ${check.url?`<a href="${escape(safeUrl(check.url))}" target="_blank" rel="noopener noreferrer">${escape(check.url)}</a>`:escape(check.tool||'research')} ${escape(check.message||check.catalog_price_note||'Page read; prices and availability still need confirmation.')}</p>`).join('')}</details>`:'';
  $('agent-results').innerHTML=notes+warnings+checks+recommendations+(!result.recommendations.length?'<div class="research-message">No supported combination fits these constraints. Get new quotes or adjust the format, budget or set-aside while keeping your guest-list priority.</div>':'')+rejected+leads;
}

function notify(text) { $('toast').textContent=text; $('toast').hidden=false; clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3500); }
function persist() {try {localStorage.setItem(STORAGE,JSON.stringify({party,selected,quotes,saved,extras}));}catch {notify('Browser storage is unavailable. Download your shortlist before leaving.');}}
function allOptions() {return [...catalog.venues,...catalog.decorators,...extras];}
function chosen() {return ['venue','decorator'].map(kind=>allOptions().find(o=>o.id===selected[kind])).filter(Boolean);}
function showDialog(id) {$(id).showModal();document.body.classList.add('modal-open');}
function closeDialog(dialog) {dialog.close();document.body.classList.remove('modal-open');}
document.querySelectorAll('dialog').forEach(dialog=>{
  dialog.querySelector('[data-close]')?.addEventListener('click',()=>closeDialog(dialog));
  dialog.addEventListener('close',()=>document.body.classList.remove('modal-open'));
  dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)closeDialog(dialog);}});
});

function renderBrief() {
  $('party-title').textContent=party.title;
  $('brief-date').textContent=new Date(party.date+'T12:00:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'});
  $('brief-guests').innerHTML=`${party.guests} people <span>· ${party.children} children</span>`;
  $('brief-budget').textContent=money(party.budget);
  $('total-budget').textContent=money(party.budget);
  $('reserve').value=party.reserve;
  const note=document.querySelector('.planning-note p');
  note.textContent=`For ${party.guests} people, start with a flexible space and one beautiful decor focal point. Keep room in your budget for food, cake, games and required fees.`;
  $('saved-count').textContent=saved.length;
  document.querySelector('.sidebar-footnote').textContent=`A shortlist, not a booking. All-in prices, Stitch designs and availability on ${party.date} need provider confirmation.`;
}

function card(option) {
  const selectedHere=selected[option.kind]===option.id;
  const isSaved=saved.includes(option.id);
  const capacity=option.kind==='venue' ? (option.capacity ? `Up to ${option.capacity} people` : 'Capacity to confirm') : 'Stitch design to confirm';
  const price=option.price==null ? 'Quote required' : `${money(option.price)} <small>${option.price_type==='starting_at' ? 'starting at' : 'base rental'}</small>`;
  return `<article class="option-card ${selectedHere?'is-selected':''}" data-option="${escape(option.id)}">
    <div class="card-photo" data-details="${escape(option.id)}" role="button" tabindex="0" aria-label="View ${escape(option.name)} details">
      <img src="${escape(option.image || '/assets/navajo.jpg')}" alt="${escape(option.image ? option.name+' — photo from the provider website' : 'Illustrative community venue; not a photo of this researched venue')}" loading="lazy">
      <span class="card-badge">${escape(option.badge || 'Web-researched option')}</span><button class="save-button" data-save="${escape(option.id)}" aria-label="${isSaved?'Unsave':'Save'} ${escape(option.name)}" aria-pressed="${isSaved}">${isSaved?'♥':'♡'}</button>
      <span class="photo-attribution">${escape(option.image ? option.image_credit : 'Illustrative only')}</span>
    </div>
    <div class="card-content"><div class="card-location"><span>⌖ ${escape(option.area)}</span><span>${escape(capacity)}</span></div>
      <h3>${escape(option.name)}</h3><p class="card-description">${escape(option.description)}</p>
      <div class="features">${option.features.map(feature=>`<span class="feature">${escape(feature)}</span>`).join('')}</div>
      <div class="price-row"><div><div class="price">${price}</div><p class="price-context">${option.kind==='venue'?'Required security & other fees extra':'Custom theme & extras need a quote'}</p></div><button class="card-details" data-details="${escape(option.id)}">Details ↗</button></div>
      <div class="card-footer"><button class="select-button" data-select="${escape(option.id)}">${selectedHere?'✓ Selected for your party':option.kind==='venue'?'Choose this venue':'Choose this decorator'}</button></div>
      <a class="source-link" href="${escape(safeUrl(option.source_url))}" target="_blank" rel="noopener noreferrer">View official source ↗</a>
    </div></article>`;
}

function renderCards() {
  const options=category==='venues' ? [...catalog.venues,...extras] : catalog.decorators;
  let results=filteredOptions(options,{guests:party.guests,search:$('search').value});
  if(onlySaved)results=results.filter(o=>saved.includes(o.id));
  if($('sort').value==='price')results.sort((a,b)=>(a.price??Infinity)-(b.price??Infinity));
  if($('sort').value==='capacity')results.sort((a,b)=>(b.capacity??0)-(a.capacity??0));
  $('cards').innerHTML=results.length ? results.map(card).join('') : '<div class="empty-state"><h3>A little more exploring?</h3><p>No options match these filters and your guest count. Try another search, clear Saved, or research another venue.</p><button class="button button-outline" id="clear-filters">Clear filters</button></div>';
  $('results-count').textContent=`${results.length} ${onlySaved?'saved ':''}${category==='venues'?'venue':'decorator'} option${results.length===1?'':'s'} ${category==='venues'?`for ${party.guests} guests`:''}`;
  $('options-title').textContent=category==='venues'?'Good spaces. Happy faces.':'A little extra magic.';
  $('options-subtitle').textContent=category==='venues'?'A few local places to start your celebration.':'Professional touches for her very own Stitch-inspired celebration.';
  $('catalog-note').textContent=category==='venues'?'Published capacities are maximums, not confirmed party layouts. Check room for tables and children’s games before choosing.':'Photos show each provider’s past work, not a promised Stitch package. Starting rates do not include every item, installation or delivery.';
  $('venue-count').textContent=catalog.venues.length+extras.length;
  $('decorator-count').textContent=catalog.decorators.length;
  $('saved-filter').setAttribute('aria-pressed',String(onlySaved));
  document.querySelectorAll('[data-category]').forEach(button=>{
    button.classList.toggle('active',button.dataset.category===category);
    button.setAttribute('aria-selected',String(button.dataset.category===category));
  });
}

function renderPlan() {
  $('selected-options').innerHTML=['venue','decorator'].map(kind=>{
    const option=allOptions().find(o=>o.id===selected[kind]);
    if(!option)return `<div class="selection-slot"><span class="slot-icon">${kind==='venue'?'⌂':'✧'}</span><div class="slot-label">${kind==='venue'?'A space for everyone':'A little birthday magic'}<small>Choose a ${kind==='venue'?'venue':'professional decorator'} to start</small></div></div>`;
    const quote=quotes[option.id];
    return `<div class="selection-slot chosen-slot"><img src="${escape(option.image||'/assets/navajo.jpg')}" alt=""><div class="slot-label">${escape(option.name)}<small>${option.price==null?'Quote required':`Published ${kind==='venue'?'base':'minimum'} ${money(option.price)}`}</small><label class="quote-input-label">Your all-in quote ($)<input type="number" min="0" max="1000000" step="0.01" placeholder="Not confirmed" data-quote="${escape(option.id)}" value="${Number.isFinite(quote)?quote:''}"></label></div><button class="remove-selection" data-remove="${kind}" aria-label="Remove ${escape(option.name)}">×</button></div>`;
  }).join('');
  updateBudget();
}

function updateBudget() {
  const options=chosen(),summary=budgetSummary(party,options,quotes);
  $('selected-total').textContent=options.length?money(summary.subtotal):'—';
  $('subtotal-label').textContent=summary.complete?'Based on the all-in quotes you entered; confirm their terms.':options.length?'Published base/minimum only. Missing quotes and extras are not included.':'Choose your options to see their starting costs.';
  $('headroom').textContent=options.length?money(summary.headroom):'—';
  $('budget-fill').style.width=Math.min(100,summary.subtotal/party.budget*100)+'%';
  const states={choose_options:'Your choices will appear here.',quotes_needed:'Quotes needed. Published starting costs cannot confirm your whole-party budget.',over_budget:'These costs plus your set-aside exceed your budget. Choose a simpler setup or revise the plan.',tight:'A tight fit with your set-aside. Check every fee before committing.',within_allowance:'Within your entered allowance. Date availability and package terms still need confirmation.'};
  $('budget-status').textContent=states[summary.status];
  $('budget-status').className='budget-status'+(summary.status==='over_budget'?' over':['quotes_needed','tight'].includes(summary.status)?' warn':'');
}

function selectOption(id) {
  const option=allOptions().find(o=>o.id===id);if(!option)return;
  selected[option.kind]=id;persist();renderCards();renderPlan();
  notify(`${option.name} added to your party.`);
}

function showDetails(id) {
  const option=allOptions().find(o=>o.id===id);if(!option)return;
  const questions=option.confirm.map(x=>/availability/i.test(x)?`Availability on ${party.date}`:x);
  const evidence=option.facts?`<div class="detail-section"><h3>Published page excerpts</h3>${Object.entries(option.facts).filter(([key,value])=>key!=='amenities'&&value).map(([key,value])=>`<p class="detail-meta"><strong>${escape(key)}:</strong> ${escape(value.evidence)}</p>`).join('')}</div>`:'';
  $('details-body').innerHTML=`${option.image?`<img class="detail-photo" src="${escape(option.image)}" alt="${escape(option.name)} — provider portfolio photo">`:''}<span class="eyebrow">${option.kind==='venue'?'A SPACE FOR EVERYONE':'PROFESSIONAL DECOR'}</span><h2 id="details-title">${escape(option.name)}</h2><p>${escape(option.description)}</p><p class="detail-meta">${escape(option.address||option.package||'San Antonio service area')} · Source checked ${escape(option.checked_on)}${option.image?` · Photo: ${escape(option.image_credit)}`:''}</p><div class="detail-price"><strong>${option.price==null?'Quote required':money(option.price)}</strong><span>${escape(option.price_note)}<br>Availability on ${escape(party.date)} is unconfirmed.</span></div><div class="detail-section"><h3>${option.kind==='venue'?'Published amenities':'Services to discuss'}</h3><ul>${option.features.map(x=>`<li>${escape(x)}</li>`).join('')}</ul>${option.kind==='venue'?`<p class="detail-meta">Published capacity: ${escape(option.capacity??option.capacity_text??'unknown')}. Seated games layout for ${party.guests} people needs confirmation.</p>`:'<p class="detail-meta">Stitch-specific designs and included character pieces are not yet confirmed.</p>'}</div><div class="detail-section"><h3>Not included in this displayed price</h3><ul>${option.exclusions.map(x=>`<li>${escape(x)}</li>`).join('')}</ul></div><div class="detail-section"><h3>Ask before choosing</h3><ul>${questions.map(x=>`<li>${escape(x)}</li>`).join('')}</ul></div>${evidence}<button class="button button-dark" data-modal-select="${escape(option.id)}">Add to my party ↗</button> <a class="button button-outline" href="${escape(safeUrl(option.source_url))}" target="_blank" rel="noopener noreferrer">Source website ↗</a>`;
  if(option.contact){
    const contact=option.contact;
    const phone=/^\+[1-9]\d{7,14}$/.test(contact.phone_e164||'')?`<p><a href="tel:${escape(contact.phone_e164)}">${escape(contact.phone_display)}</a></p>`:'';
    $('details-body').querySelector('[data-modal-select]').insertAdjacentHTML('beforebegin',`<div class="detail-section"><h3>Contact the reservations office</h3><p>${escape(contact.organization)}</p><p class="detail-meta">${escape(contact.role)}</p>${phone}<p>${escape(contact.office_hours)} · Central time</p><p class="detail-meta">Direct email not verified. Contact checked ${escape(contact.verified_on)}.</p><a href="${escape(safeUrl(contact.contact_url))}" target="_blank" rel="noopener noreferrer">Official contact page ↗</a></div>`);
  }
  showDialog('details-dialog');
}

function download(data,filename,type) {
  const url=URL.createObjectURL(new Blob([data],{type}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}

async function init() {
  try {
    const response=await fetch('/party/catalog');if(!response.ok)throw Error('Catalog unavailable');catalog=await response.json();party={...catalog.party};
    try {const stored=JSON.parse(localStorage.getItem(STORAGE)||'null');if(stored){
      if(stored.party&&typeof stored.party.title==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(stored.party.date)&&Number.isFinite(stored.party.budget)&&stored.party.budget>0&&Number.isInteger(stored.party.guests)&&stored.party.guests>0&&Number.isFinite(stored.party.reserve)&&stored.party.reserve>=0)party={...party,...stored.party,city:'San Antonio, Texas',theme:'Stitch'};
      selected=stored.selected&&typeof stored.selected==='object'?stored.selected:{};
      quotes=stored.quotes&&typeof stored.quotes==='object'?stored.quotes:{};
      saved=Array.isArray(stored.saved)?stored.saved.filter(x=>typeof x==='string'):[];
      extras=Array.isArray(stored.extras)?stored.extras.filter(o=>o&&typeof o.name==='string'&&typeof o.id==='string'&&Array.isArray(o.features)&&Array.isArray(o.exclusions)&&Array.isArray(o.confirm)):[];
    }}catch{ /* Ignore corrupt browser state; begin with the birthday brief. */ }
    renderBrief();renderCards();renderPlan();
  }catch { $('cards').innerHTML='<div class="empty-state"><h3>We couldn’t load the local options.</h3><p>Check that CONVENE’s API is running, then refresh this page.</p></div>';$('results-count').textContent='Catalog unavailable';return; }

  document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;renderCards();}));
  $('cards').addEventListener('click',event=>{
    const save=event.target.closest('[data-save]');if(save){event.stopPropagation();const id=save.dataset.save;saved=saved.includes(id)?saved.filter(x=>x!==id):[...saved,id];persist();renderBrief();renderCards();return;}
    const select=event.target.closest('[data-select]');if(select){selectOption(select.dataset.select);return;}
    const details=event.target.closest('[data-details]');if(details)showDetails(details.dataset.details);
    if(event.target.id==='clear-filters'){$('search').value='';onlySaved=false;renderCards();}
  });
  $('cards').addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)&&event.target.matches('.card-photo')){event.preventDefault();showDetails(event.target.dataset.details);}});
  $('search').addEventListener('input',renderCards);$('sort').addEventListener('change',renderCards);
  $('saved-filter').addEventListener('click',()=>{onlySaved=!onlySaved;renderCards();});
  $('saved-nav').addEventListener('click',()=>{onlySaved=true;renderCards();$('browse').scrollIntoView({behavior:'smooth'});});
  $('explore-decor').addEventListener('click',()=>{category='decorators';onlySaved=false;$('search').value='';renderCards();$('browse').scrollIntoView({behavior:'smooth'});});
  $('plan-nav').addEventListener('click',()=>$('your-plan').scrollIntoView({behavior:'smooth',block:'start'}));
  $('how-it-works').addEventListener('click',()=>showDialog('how-dialog'));
  $('selected-options').addEventListener('click',event=>{const button=event.target.closest('[data-remove]');if(button){delete selected[button.dataset.remove];persist();renderCards();renderPlan();}});
  $('selected-options').addEventListener('input',event=>{if(event.target.matches('[data-quote]')){const value=event.target.valueAsNumber;if(event.target.value===''||!Number.isFinite(value)||value<0)delete quotes[event.target.dataset.quote];else quotes[event.target.dataset.quote]=value;invalidateAgent();persist();updateBudget();}});
  $('reserve').addEventListener('input',event=>{if(!event.target.validity.valid)return;party.reserve=Number(event.target.value)||0;invalidateAgent();persist();updateBudget();});
  $('details-body').addEventListener('click',event=>{const button=event.target.closest('[data-modal-select]');if(button){selectOption(button.dataset.modalSelect);closeDialog($('details-dialog'));}});
  $('edit-brief').addEventListener('click',()=>{const form=$('brief-form');for(const field of ['title','date','children','family','budget'])form.elements[field].value=party[field];showDialog('brief-dialog');});
  $('brief-form').addEventListener('submit',event=>{event.preventDefault();const data=new FormData(event.currentTarget);party={...party,title:data.get('title').trim(),date:data.get('date'),children:Number(data.get('children')),family:Number(data.get('family')),budget:Number(data.get('budget'))};party.guests=party.children+party.family;for(const option of chosen()){if(option.kind==='venue'&&option.capacity!=null&&option.capacity<party.guests){delete selected.venue;notify('Previous venue removed: its published capacity is below your updated guest count.');}}invalidateAgent();persist();renderBrief();renderCards();renderPlan();closeDialog($('brief-dialog'));});
  $('prepare-quote').addEventListener('click',()=>{const options=chosen();if(!options.length){notify('Choose a venue or decorator first.');return;}$('quote-text').value=quoteRequest(party,options);$('quote-sources').innerHTML=options.map(o=>`<a href="${escape(safeUrl(o.source_url))}" target="_blank" rel="noopener noreferrer">${escape(o.name)} ↗</a>`).join('');showDialog('quote-dialog');});
  $('copy-quote').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('quote-text').value);notify('Quote request copied. Send it to the providers when you’re ready.');}catch{$('quote-text').select();notify('Select and copy the draft text.');}});
  $('download-plan').addEventListener('click',()=>download(JSON.stringify({party,options:chosen(),entered_quotes:quotes,budget:budgetSummary(party,chosen(),quotes),notice:'A shortlist, not a booking. Starting rates are not full quotes. Date availability, custom Stitch design and required extras need provider confirmation.'},null,2),'convene-birthday-shortlist.json','application/json'));
  $('open-research').addEventListener('click',()=>showDialog('research-dialog'));
  $('research-form').addEventListener('submit',async event=>{
    event.preventDefault();const urls=$('research-urls').value.split('\n').map(x=>x.trim()).filter(Boolean),discover=$('research-discover').checked;
    if(urls.length>5||(!urls.length&&!discover)){$('research-results').innerHTML='<p class="research-message">Supply one to five public venue URLs, or enable discovery.</p>';return;}
    $('research-button').disabled=true;$('research-button').textContent='Reading venue websites…';$('research-results').innerHTML='<p class="research-message">Looking for sourced venue details. This may take up to 90 seconds.</p>';
    try{
      const response=await fetch('/venues/research',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:party.city,guests:party.guests,urls,discover}),signal:AbortSignal.timeout(100000)});
      const result=await response.json();if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Please check the URL and request details.');
      researchCandidates=result.candidates;
      $('research-results').innerHTML=result.errors.map(error=>`<p class="research-message">${escape(error.url||'Discovery')}: ${escape(error.error)}</p>`).join('')+result.candidates.map((venue,index)=>`<article class="research-venue"><h3>${escape(venue.details.name.value)}</h3><p>${escape(venue.details.address.value)}</p><p>Capacity: ${escape(venue.details.capacity?.value||'Unconfirmed')} · Pricing: ${escape(venue.details.pricing?.value||'Quote required')}</p><p>Capacity suitability for ${party.guests} people and date availability require confirmation.</p><a href="${escape(safeUrl(venue.source_url))}" target="_blank" rel="noopener noreferrer">Source website ↗</a> <button class="button button-outline" data-add-research="${index}">Add to my party ↗</button></article>`).join('')+(!result.candidates.length&&!result.errors.length?'<p class="research-message">No results. Try a different venue page.</p>':'');
    }catch(error){$('research-results').innerHTML=`<p class="research-message">${escape(error.name==='TimeoutError'?'Research timed out. Try one URL at a time.':error.message)}</p>`;}
    finally{$('research-button').disabled=false;$('research-button').textContent='Research venues ↗';}
  });
  $('research-results').addEventListener('click',event=>{
    const button=event.target.closest('[data-add-research]');if(!button)return;
    const venue=researchCandidates[Number(button.dataset.addResearch)];if(!venue)return;
    let option=allOptions().find(o=>o.source_url===venue.source_url);
    if(!option){option=researchedOption(venue,Date.now());extras.push(option);}
    category='venues';onlySaved=false;$('search').value='';selectOption(option.id);
    closeDialog($('research-dialog'));$('your-plan').scrollIntoView({behavior:'smooth'});
    notify('Venue added. Confirm capacity and an all-in quote before committing.');
  });
  $('run-agent').addEventListener('click',async()=>{
    agentController?.abort();const version=++agentVersion;agentController=new AbortController();agentResult=null;
    $('run-agent').disabled=true;$('agent-results').innerHTML='';$('agent-activity').innerHTML='';$('agent-activity').hidden=false;
    $('agent-status').textContent=$('agent-mode').value==='live'?'Agent is working. Activity below comes from actual node and tool events.':'Comparing dated catalog entries only. No web or model calls.';
    const allowedIds=new Set([...catalog.venues,...catalog.decorators].map(option=>option.id));
    const agentQuotes=Object.fromEntries(Object.entries(quotes).filter(([id,value])=>allowedIds.has(id)&&Number.isFinite(value)&&value>=0));
    try{
      const response=await fetch('/party/agent',{method:'POST',headers:{'Content-Type':'application/json'},signal:agentController.signal,
        body:JSON.stringify({mode:$('agent-mode').value,city:party.city,theme:party.theme,date:party.date,children:party.children,family:party.family,budget:party.budget,reserve:party.reserve,quotes:agentQuotes})});
      if(!response.ok){const error=await response.json();throw Error(typeof error.detail==='string'?error.detail:'Check the party details and try again.');}
      const result=await readAgentStream(response.body,event=>{
        if(version!==agentVersion)return;
        if(event.type==='node'||event.type==='tool'){
          const item=document.createElement('li');item.className='activity-'+event.status;
          const label=event.type==='tool'?`${event.node} · ${event.tool}`:event.node;
          item.textContent=`${event.status==='completed'?'✓':event.status==='failed'?'!':'→'} ${label}: ${event.message}`;
          $('agent-activity').append(item);$('agent-activity').scrollTop=$('agent-activity').scrollHeight;
          $('agent-status').textContent=event.message;
        }
      });
      if(version!==agentVersion)return;
      renderAgentResult(result);
      $('agent-status').textContent=`${result.mode==='live'?'Live run':'Catalog comparison'} finished · research: ${result.research_status.replaceAll('_',' ')} · ${result.tool_count} tool calls · ${result.recommendations.length} combinations to review. No availability or full-price guarantee.`;
    }catch(error){if(version===agentVersion)$('agent-status').textContent=error.name==='AbortError'?'Agent run cancelled.':`Agent could not finish: ${error.message}`;}
    finally{if(version===agentVersion)$('run-agent').disabled=false;}
  });
  $('agent-results').addEventListener('click',event=>{
    const button=event.target.closest('[data-agent-pair]');if(!button||!agentResult)return;
    const pair=agentResult.recommendations[Number(button.dataset.agentPair)];if(!pair)return;
    if(!allOptions().some(option=>option.id===pair.venue_id)||!allOptions().some(option=>option.id===pair.decorator_id))return;
    selected.venue=pair.venue_id;selected.decorator=pair.decorator_id;persist();renderCards();renderPlan();
    $('your-plan').scrollIntoView({behavior:'smooth'});notify('Combination added. Request all-in quotes before committing.');
  });
}
init();
