"""Offline interactive enhancements; every value comes from a validated packet."""
from datetime import date, timedelta
from functools import lru_cache
from html import escape
import json
from pathlib import Path
import re
from campaign_hub.reporting.snapshot import source_sections


def script_json(value):
    return json.dumps(value,ensure_ascii=True,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')


@lru_cache(maxsize=2)
def vendor(name):
    return (Path(__file__).parent/'vendor'/name).read_text(encoding='utf-8')


STYLE='''
.interactive-chart{height:285px;position:relative;margin:18px 0}
.interactive-chart[hidden]{display:none}.chart-ready>.static-chart{display:none}
.chart-ready>.interactive-chart{display:block}.kpi-callout{font-size:13px;font-weight:700;color:var(--teal);margin:12px 0}
.chart-reading{font-size:13px;margin-top:13px}.chart-reading p{margin:7px 0}
.status-pill{display:inline-block;margin-top:12px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:bold}
.favorable{background:#e2f2ec;color:#125943}.unfavorable{background:#fff0e9;color:#8e381c}
.availability{border:1px dashed #a8b7c2;border-radius:9px;background:#f7f9fa;padding:20px}
.availability h3{font-size:17px}.availability p{font-size:13px;margin-bottom:0}
.story-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.story-card{background:white;border:1px solid var(--line);border-radius:9px;padding:20px}
.story-card h3{font-size:17px}.story-card p{font-size:13px}.story-number{color:var(--teal);font-weight:bold}
.table-wrap{overflow-x:auto}table{width:100%;font-size:12px}th,td{padding:9px;border-bottom:1px solid var(--line);text-align:left}
.chart-card details{font-size:12px;margin:12px 0}.timeline{display:grid;gap:15px}.timeline-row{border-left:4px solid var(--teal);padding:15px;background:#eef5f5;border-radius:0 8px 8px 0;font-size:14px}
@media(max-width:750px){.story-grid{grid-template-columns:1fr}.interactive-chart{height:260px}}
@media print{.chart-ready>.static-chart{display:block}.interactive-chart{display:none!important}.story-card{break-inside:avoid}.story-grid{grid-template-columns:1fr 1fr}}
'''


def chart_runtime(panels):
    data=[{'id':'interactive-'+str(i),'labels':p['labels'],'values':p['values'],'unit':p['unit'],
           'highlights':p['highlights']} for i,p in enumerate(panels,1)]
    # Show the static chart until construction succeeds, including environments blocking scripts.
    runtime='''
(() => {
 const panels=PAYLOAD;
 for(const p of panels){
  const canvas=document.getElementById(p.id);if(!canvas)continue;
  try {
   const view=canvas.parentElement;view.hidden=false;
   new Chart(canvas,{type:'bar',data:{labels:p.labels,datasets:[{label:p.unit,data:p.values,
    backgroundColor:p.values.map((_,i)=>p.highlights.includes(i)?'#087f80':'#8ba0af'),borderRadius:4}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:false,
     plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>p.unit==='percent'?
       (c.raw*100).toFixed(2)+'%':p.unit==='USD'?'$'+c.raw.toLocaleString(undefined,{maximumFractionDigits:2}):c.raw.toLocaleString()}}},
     scales:{x:{beginAtZero:true,ticks:{callback:v=>p.unit==='percent'?(v*100).toFixed(1)+'%':p.unit==='USD'?'$'+v.toLocaleString():v}},y:{grid:{display:false}}}}});
   canvas.closest('.chart-card').classList.add('chart-ready');
  }catch(error){canvas.parentElement.hidden=true;}
 }
})();
'''.replace('PAYLOAD',script_json(data))
    library=vendor('chart.umd.min.js').replace('</script','<\\/script')
    return '<script>'+library+'</script><script>'+runtime+'</script>'


def table(panel):
    from campaign_hub.reporting.visuals import value_label
    return '<details><summary>View chart data</summary><div class="table-wrap"><table><caption>'+escape(panel['title'])+'</caption><thead><tr><th scope="col">Category</th><th scope="col">Value</th></tr></thead><tbody>'+''.join(
        '<tr><th scope="row">'+escape(label)+'</th><td>'+escape(value_label(value,panel['unit']))+'</td></tr>'
        for label,value in zip(panel['labels'],panel['values']))+'</tbody></table></div></details>'


def reading(panel):
    actions={
        'Progress Toward Goals':'Use the goal variance to set the next campaign test; confirm acquisition quality before expanding spend.',
        'Channel performance':'Test channel allocation with a controlled design before claiming incremental advantage.',
        'Same-client historical standing':'Use the matched cohort as descriptive context; expand the comparable sample before generalizing.',
        'Geographic performance':'Check local exposure coverage before using outcome concentration to change geographic investment.',
        'Audience insights':'Collect segment-specific exposure counts before comparing audience conversion rates.'}
    return '<div class="chart-reading"><p><strong>Why / evidence boundary:</strong> Observational totals describe associations. These sources do not establish causal effects.</p><p><strong>Recommended action (proposed):</strong> '+escape(actions[panel['family']])+'</p></div>'


def kpi_cards(packet,citations):
    f=packet['facts']; result=['<div class="stats">']
    metrics=[('Attributed accounts',f['actual'],f['target'],'accounts',True),
        ('Opening balances',f['balance_cents']/100,f['balance_target_cents']/100,'USD',True),
        ('Attributed spend',f['spend'],f['budget'],'USD',False),
        ('Cost per activation',f['spend']/f['actual'],f['budget']/f['target'],'USD',False)]
    from campaign_hub.reporting.visuals import value_label
    for label,value,target,unit,higher in metrics:
        good=value>=target if higher else value<=target
        variance=value-target;percentage=variance/target if target else None
        result.append('<div class="stat"><div class="stat-label">'+label+'</div><strong>'+value_label(value,unit)+'</strong><small>Target '+value_label(target,unit)+
            '<br>Variance '+('+' if variance>=0 else '−')+value_label(abs(variance),unit)+(' ('+f'{percentage:+.1%}'+')' if percentage is not None else '')+
            '</small><br><span class="status-pill '+('favorable' if good else 'unfavorable')+'">'+('Favorable' if good else 'Below goal' if higher else 'Above ceiling')+'</span></div>')
    return ''.join(result)+'</div>'+citations([packet['campaign_id']+'-performance_report',packet['campaign_id']+'-success_plan'])


def audience_panel(packet):
    text=source_sections(packet['sources'],packet['campaign_id'],'performance_report').get('Audience Insights','')
    match=re.search(r'Existing members supplied (\d+) activations and prospective members (\d+)',text)
    if not match or sum(map(int,match.groups()))!=packet['facts']['actual']:
        return None
    return dict(key='audience',family='Audience insights',title='Audience composition',
        labels=['Existing members','Prospective members'],values=list(map(int,match.groups())),unit='accounts',
        highlights=[0,1],insight=text,citations=[packet['campaign_id']+'-performance_report'],
        note='Outcome counts only; segment exposure counts and causal drivers were not measured.')


def supplemental(packet,citations,audience_html):
    f=packet['facts']; cid=packet['campaign_id'];out=['<section id="audience"><div class="section-head"><span>06</span><h2>Audience insights</h2></div>',audience_html,'</section>',
        '<section id="timeline"><div class="section-head"><span>07</span><h2>Attribution timeline</h2></div><div class="timeline">']
    for channel,s in f['channel_results'].items():
        end=date.fromisoformat(s['anchor_date'])+timedelta(days=s['window_days'])
        out.append('<div class="timeline-row"><strong>'+escape(channel.replace('_',' ').title())+'</strong><br>'+escape(s['anchor'].replace('_',' ').title())+': '+s['anchor_date']+' → '+end.isoformat()+
            f' · {s["window_days"]} elapsed days<br>Results observed through '+s['as_of']+'</div>')
    out.extend(['</div><p class="chart-reading"><strong>What happened:</strong> Both attribution windows are fully observed. <strong>Why:</strong> The source as-of dates follow the final attribution dates. <strong>Recommended action:</strong> Keep these definitions consistent in the next comparison.</p>',citations([cid+'-performance_report',cid+'-success_plan']),'</section>',
        '<section id="availability"><div class="section-head"><span>08</span><h2>Measurement coverage</h2></div><div class="panel-grid">'])
    missing=[('Deposit growth trend','Only opening balances are recorded; net deposit growth and dated balance observations are absent.'),
        ('Account opening trend','Only period totals are recorded; daily or monthly account-opening dates are absent.'),
        ('Funded account trend','A separate funded-account flag and funding dates are absent.'),
        ('Conversion funnel','Impressions, clicks, applications and funding stages are absent. Mail households and display users are distinct denominators.'),
        ('Financial ROI','Incremental revenue, margin and a counterfactual are absent. Opening balances are not revenue.')]
    for title,reason in missing:
        out.append('<div class="availability"><h3>'+title+'</h3><strong>Unavailable</strong><p>'+reason+'</p></div>')
    out.extend(['</div>',citations([cid+'-performance_report']),'</section>'])
    return ''.join(out)


def storyline(packet,citations):
    items=[('Campaign overview','summary','Client, campaign, period and attributed outcomes.'),
        ('Objectives','goals','Targets and success criteria from the approved success plan.'),
        ('Performance dashboard','goals','Goal attainment, balances, acquisition cost and historical standing.'),
        ('Audience insights','audience','Observed segment counts and limits of audience measurement.'),
        ('Channel performance','channels','Direct mail and display contributions with distinct attribution windows.'),
        ('Recommendations','actions','Source-backed proposed tests; projected impact is unmeasured.'),
        ('Next steps','actions','Agree action owners and dates; retain measurement definitions.')]
    out=['<section id="storyline"><div class="section-head"><span>10</span><h2>Presentation storyline</h2></div><div class="story-grid">']
    for i,(title,anchor,text) in enumerate(items,1):
        out.append(f'<div class="story-card"><div class="story-number">{i:02}</div><h3><a href="#{anchor}">{title}</a></h3><p>{text}</p></div>')
    out.extend(['</div>',citations(packet['sections'][0]['citations']+packet['sections'][4]['citations']),'</section>'])
    return ''.join(out)
