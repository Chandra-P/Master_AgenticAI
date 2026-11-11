'use strict';
const DATA=JSON.parse(document.getElementById('report-data').textContent);
const $=id=>document.getElementById(id);
const num=v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:0});
const money=v=>v===null?'Not yet available':Number(v).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let mapMeasure='accounts',shareMeasure='accounts';
const card=(label,value,sub)=>'<div class="card"><div class="label">'+escape(label)+'</div><div class="value">'+escape(value)+'</div><div class="sub">'+escape(sub)+'</div></div>';
function table(id,headers,rows){
 const el=$(id);el.replaceChildren();
 const head=document.createElement('tr');
 headers.forEach(t=>{const c=document.createElement('th');c.textContent=t;head.append(c);});el.append(head);
 rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td);});el.append(tr);});
}
function svg(tag,attrs,text){
 const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
 Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;return e;
}
function map(f){
 const el=$('branch-map');el.replaceChildren();
 $('map-detail').textContent='Select a branch marker to inspect its results.';
 // Abstract topology is deliberately fictional; no external map tiles or addresses.
 for(let x=50;x<900;x+=100)el.append(svg('path',{d:'M '+x+' 0 L '+(x-70)+' 430',stroke:'#d5ddd3','stroke-width':18,fill:'none'}));
 el.append(svg('path',{d:'M 0 350 Q 200 190 400 270 T 900 100',stroke:'#b8d2d5','stroke-width':22,fill:'none'}));
 const max=Math.max(1,...f.branches.map(b=>Number(b[mapMeasure])));
 f.branches.forEach((b,i)=>{
  const x=95+(i%4)*215+(i%2)*12,y=75+Math.floor(i/4)*137;
  const radius=12+Number(b[mapMeasure])/max*19;
  const marker=svg('circle',{cx:x,cy:y,r:radius,fill:'#155a76',stroke:'white','stroke-width':3,tabindex:0,role:'button','aria-label':b.name});
  const show=()=>{$('map-detail').textContent=b.name+': '+num(b.accounts)+' accounts · '+money(b.balance)+' balances · '+Number(b.response_rate).toFixed(3)+'% of '+num(b.households)+' households.';};
  marker.addEventListener('click',show);marker.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show();}});el.append(marker);
  el.append(svg('text',{x,y:y+49,'text-anchor':'middle',fill:'#063b54','font-size':12},b.name));
 });
}
function fairShare(f){
 const host=$('fair-share');host.replaceChildren();
 f.branches.slice().sort((a,b)=>Number(b.fair_share_accounts)-Number(a.fair_share_accounts)).forEach(b=>{
  const row=document.createElement('div');row.className='share-row';
  const label=document.createElement('span');label.textContent=b.name;row.append(label);
  const bars=document.createElement('div');
  const keys=shareMeasure==='both'?['fair_share_accounts','fair_share_balance']:[shareMeasure==='balance'?'fair_share_balance':'fair_share_accounts'];
  keys.forEach((key,i)=>{const bar=document.createElement('div');bar.className='share-bar'+(i?' secondary':'');bar.style.width=Math.min(100,Number(b[key])/2.5*100)+'%';bars.append(bar);});row.append(bars);
  const value=document.createElement('span');value.textContent=keys.map(k=>Number(b[k]).toFixed(2)+'×').join(' / ');row.append(value);host.append(row);
 });
}
function forecast(f){
 const el=$('forecast-chart');el.replaceChildren();
 const goal=DATA.config.checking_goal,max=Math.max(f.forecast_high,goal,1)*1.2;
 const y=v=>310-v/max*270;
 el.append(svg('line',{x1:70,y1:310,x2:850,y2:310,stroke:'#bfcac8'}));
 el.append(svg('line',{x1:70,y1:y(goal),x2:850,y2:y(goal),stroke:'#b65a22','stroke-dasharray':'7 5'}));
 el.append(svg('text',{x:75,y:y(goal)-10,fill:'#b65a22','font-size':13},'Goal '+num(goal)));
 el.append(svg('polygon',{points:'190,'+y(f.checking_accounts)+' 800,'+y(f.forecast_high)+' 800,'+y(f.forecast_low),fill:'#d7e7e6'}));
 el.append(svg('line',{x1:190,y1:y(f.checking_accounts),x2:800,y2:y(f.forecast),stroke:'#155a76','stroke-width':4}));
 el.append(svg('circle',{cx:190,cy:y(f.checking_accounts),r:7,fill:'#063b54'}));
 el.append(svg('text',{x:190,y:340,'text-anchor':'middle',fill:'#063b54','font-size':14},'Observed '+num(f.checking_accounts)));
 el.append(svg('text',{x:800,y:340,'text-anchor':'middle',fill:'#063b54','font-size':14},'Finish '+num(f.forecast)));
 el.append(svg('text',{x:800,y:25,'text-anchor':'middle',fill:'#155a76','font-size':14},num(f.forecast_low)+'–'+num(f.forecast_high)));
}
function paint(){
 const period=$('period').value,f=DATA.periods[period],c=DATA.config;
 $('read-date').textContent=(period==='F'?'Final':period+' day')+' read · '+f.as_of;
 $('hero-result').textContent=num(f.checking_accounts)+' Checking accounts and '+num(f.new_members)+' new members confirmed.';
 $('hero-outlook').textContent=period==='F'?'Final results are recorded.':num(f.forecast)+' Checking accounts projected; range '+num(f.forecast_low)+'–'+num(f.forecast_high)+'.';
 $('goal-cards').innerHTML=card('Checking accounts',num(c.checking_goal),'Distinct qualifying open and funded accounts')+card('New members',num(c.member_goal),'Any qualifying product; distinct members')+card('CPA ceiling',money(c.cpa_ceiling),'Full campaign budget: '+money(c.budget));
 $('actual-cards').innerHTML=card('Checking accounts',num(f.checking_accounts),Math.round(f.checking_accounts/c.checking_goal*100)+'% of goal')+card('New members',num(f.new_members),Math.round(f.new_members/c.member_goal*100)+'% of goal')+card('Cost per account',money(f.cpa),'Available at day 120 or later after every component launches');
 $('progress').innerHTML=[['Checking',f.checking_accounts,c.checking_goal],['New members',f.new_members,c.member_goal]].map(([label,v,goal])=>'<div class="progress-row"><b>'+label+'</b><div class="track"><div class="fill" style="width:'+Math.min(100,v/goal*100)+'%"></div></div><span>'+num(v)+' / '+num(goal)+'</span></div>').join('');
 $('happening-fact').textContent=num(f.checking_accounts)+' accounts observed versus '+num(f.expected)+' expected by the synthetic historical completion pattern. Recorded balances total '+money(f.balance)+'.';
 const guidance=period==='F'?'Final read: no future response is projected. Late corrections require a new reviewed version.':'This is a historical as-of snapshot. Only accounts and matches observed by '+f.as_of+' contribute. Future-period records are excluded. CPA is gated separately.';
 $('read-guidance').textContent=guidance;$('appendix-read').textContent=guidance;
 $('forecast-cards').innerHTML=card('Projected Checking finish',num(f.forecast),'Scenario range '+num(f.forecast_low)+'–'+num(f.forecast_high))+card('Expected by this read',num(f.expected),'Synthetic historical completion pattern')+card('Remaining to goal',num(Math.max(0,c.checking_goal-f.checking_accounts)),'Checking accounts still needed');
 $('method').textContent=f.method+' '+f.limitations.join(' ');
 const short=f.forecast_low<c.checking_goal;
 $('recommendation-title').textContent=period==='F'?'Close the campaign and preserve the evidence.':short?'The lower scenario remains below commitment.':'The historical scenario range clears the Checking goal.';
 const recommendation=period==='F'?'Review final accounts, distinct new members and CPA independently before signing off.':short?'Validate source completeness and monitor response through the remaining tracking windows. Review options with the analyst; exposure overlap alone does not justify additional digital spend.':'Continue monitoring source completeness and the separate new-member commitment. Keep the current plan under review.';
 $('recommendation').textContent=recommendation;
 $('executive-cards').innerHTML=card('Checking result',num(f.checking_accounts),'Goal '+num(c.checking_goal))+card('New-member result',num(f.new_members),'Goal '+num(c.member_goal))+card('Campaign CPA',money(f.cpa),'Ceiling '+money(c.cpa_ceiling));
 $('executive-facts').textContent=f.as_of+': '+num(f.checking_accounts)+' Checking accounts, '+num(f.new_members)+' new members; '+money(f.balance)+' recorded balances.';
 $('narrative').textContent=DATA.summary;$('executive-action').textContent=recommendation;
 $('correction').textContent=DATA.correction?'Correction version: recalculated from changed source, configuration, rules or computation.':'Initial version from a pinned synthetic source snapshot.';
 const calendar='Digital: '+c.digital_start+' to '+c.digital_end+'. Mailing 1 in-home: '+c.in_home[0]+'. Mailing 2 in-home: '+c.in_home[1]+'. Final report: '+c.final_date+'.';
 $('timeline').textContent=calendar;$('mail-calendar').textContent=calendar+' Each mailing reaches '+num(c.audience_size)+' of the same households; '+num(c.digital_reach)+' households receive digital exposure.';
 table('channel-table',['Channel','Accounts','Share'],Object.entries(f.channels).map(([k,v])=>[k,num(v),f.checking_accounts?(v/f.checking_accounts*100).toFixed(1)+'%':'—']).concat([['Total',num(f.checking_accounts),'100%']]));
 table('branch-table',['Branch','Households','Checking','Balances','CPA'],f.branches.map(b=>[b.name,num(b.households),num(b.accounts),money(b.balance),money(b.cpa)]));
 table('zip-table',['ZIP','Area','Households','Checking','Expected'],f.branches.map(b=>[b.zip_code,b.name,num(b.households),num(b.accounts),Number(b.expected).toFixed(1)]));
 table('mix-table',['Product','Accounts'],Object.entries(f.product_mix).map(([k,v])=>[k,num(v)]));
 $('halo').textContent=num(f.direct_members)+' new members opened Checking; '+num(f.halo_members)+' additional new members opened other products without a qualifying Checking account. Total: '+num(f.new_members)+'.';
 $('sources').textContent='Generated synthetic core-account history, matchback new-member classification, DM responses and TU-style exposure records. Configuration and rules: '+c.rules_version+'. Report version '+DATA.version+'. '+f.method;
 map(f);fairShare(f);forecast(f);
}
$('period').addEventListener('change',paint);
document.querySelectorAll('[data-map]').forEach(b=>b.addEventListener('click',()=>{mapMeasure=b.dataset.map;document.querySelectorAll('[data-map]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});map(DATA.periods[$('period').value]);}));
document.querySelectorAll('[data-share]').forEach(b=>b.addEventListener('click',()=>{shareMeasure=b.dataset.share;document.querySelectorAll('[data-share]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b?'true':'false');});fairShare(DATA.periods[$('period').value]);}));
$('print-report').addEventListener('click',()=>{document.querySelectorAll('details').forEach(d=>d.open=true);window.print();});
if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting)document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id));});},{rootMargin:'-20% 0px -65% 0px'});document.querySelectorAll('section').forEach(s=>observer.observe(s));}
paint();
