"""Standalone, responsive client presentation with embedded SVG charts and evidence."""
from html import escape
from math import ceil,floor,log10
from itertools import groupby
from campaign_hub.reporting.client_packet import validate_packet
from campaign_hub.reporting.snapshot import source_metadata
from campaign_hub.reporting.visuals import comparison_panels,value_label
from campaign_hub.reporting import dashboard


CSS='''
:root{--navy:#10263d;--teal:#087f80;--muted:#607587;--line:#dce5ea;--paper:#f0f3f5;--soft:#eaf5f3}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:85px}body{margin:0;background:var(--paper);color:var(--navy);font:16px/1.6 Arial,Helvetica,sans-serif}
a{color:var(--teal)}a:focus-visible,summary:focus-visible,.bar:focus-visible{outline:3px solid #d49b43;outline-offset:4px}
.wrap{max-width:1240px;margin:auto;padding:0 34px}.hero{background:var(--navy);color:#fff;padding:36px 0 60px;border-bottom:6px solid var(--teal)}
.brand{font-size:12px;text-transform:uppercase;letter-spacing:2px;color:#a8c5d2}.hero-top{display:flex;justify-content:space-between;align-items:center;gap:20px}.badge{font-size:11px;letter-spacing:1px;background:#234359;color:#b9e8e1;border:1px solid #3b6472;border-radius:5px;padding:7px 11px}
.eyebrow{font-size:12px;letter-spacing:1.8px;text-transform:uppercase;color:var(--teal);font-weight:700}.hero .eyebrow{color:#78d1c7;margin-top:45px}.hero h1{font-size:clamp(32px,4vw,52px);line-height:1.12;max-width:820px;margin:12px 0 20px;letter-spacing:-1.5px}.client{font-size:23px;margin:0 0 7px}.hero-meta{color:#c1d1dc;font-size:14px}.hero-rule{width:60px;height:3px;background:#67cfc4;margin:24px 0}.hero p.lead{max-width:680px;color:#dae5ec;margin-bottom:0}
nav{position:sticky;top:0;z-index:10;background:#ffffffed;backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}nav .wrap{display:flex;gap:25px;overflow:auto;white-space:nowrap;padding-top:15px;padding-bottom:15px}nav a{text-decoration:none;color:#344c60;font-size:13px;font-weight:700}nav a:hover{color:var(--teal)}
main{padding-bottom:45px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:30px 0}.stat{background:white;border:1px solid var(--line);border-radius:10px;padding:23px 20px;border-top:3px solid var(--teal)}.stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}.stat strong{display:block;font-size:30px;line-height:1.3;margin:8px 0}.stat small{font-size:12px;color:var(--muted)}
section{margin:40px 0;scroll-margin-top:80px}.section-head{display:flex;align-items:baseline;gap:16px;border-bottom:1px solid #cbd9e1;margin-bottom:20px;padding-bottom:13px}.section-head span{color:var(--teal);font-size:13px;font-weight:700}.section-head h2{margin:0;font-size:26px;letter-spacing:-.6px}.section-intro{color:var(--muted);max-width:850px;font-size:14px;margin-top:-5px;margin-bottom:23px}
.panel-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:23px}.chart-card{background:#fff;border:1px solid var(--line);border-radius:11px;padding:25px;overflow:hidden;box-shadow:0 4px 15px #183b5010;margin:0;display:flex;flex-direction:column}.chart-card h3{margin:0 0 5px;font-size:19px;line-height:1.3}.chart-unit{color:var(--muted);font-size:12px}.chart-card svg{display:block;width:100%;height:auto;margin:20px 0 8px;overflow:visible}.chart-note{font-size:11px;color:var(--muted);margin:4px 0 15px;line-height:1.5}.insight{background:var(--soft);border-left:3px solid var(--teal);padding:16px 17px;margin-top:auto;border-radius:0 6px 6px 0}.insight h4{font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--teal);margin:0 0 7px}.insight p{font-size:14px;line-height:1.65;margin:0}.citations{font-size:11px;color:var(--muted);margin-top:13px}.citations a{padding:2px 4px}.bar rect{transition:opacity .15s}.bar:hover rect,.bar:focus rect{opacity:.72}.copy-card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:25px 28px}.copy-card p{font-size:14px}.copy-card p:first-child{margin-top:0}.callout{border-left:3px solid #ce9b50;background:#fff8eb;padding:17px 20px;font-size:13px;margin:18px 0}.actions{display:grid;grid-template-columns:1fr 1fr;gap:23px}.actions h3{font-size:20px;margin-top:0}.source-list{padding:0;list-style:none}.source-list li{padding:20px 0;border-top:1px solid var(--line);font-size:13px;scroll-margin-top:95px}.source-list li:first-child{border-top:0}.source-number{color:var(--teal);font-weight:700;margin-right:7px}.source-meta{font-size:11px;color:var(--muted);margin-top:5px}.source-list details{margin-top:12px}.source-list summary{cursor:pointer;font-size:12px;color:var(--teal)}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f8;padding:17px;border-radius:6px;font:11px/1.6 Consolas,monospace;max-height:400px;overflow:auto}.provenance{font-size:12px;color:var(--muted);overflow-wrap:anywhere}footer{border-top:1px solid var(--line);padding:25px 0;font-size:12px;color:var(--muted)}
@media(max-width:900px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.panel-grid,.actions{grid-template-columns:1fr}.hero h1{font-size:38px}}
@media(max-width:520px){.wrap{padding:0 18px}.hero{padding-top:24px}.hero-top{align-items:flex-start;flex-direction:column}.hero .eyebrow{margin-top:30px}.hero h1{font-size:32px}.client{font-size:19px}.stat{padding:16px 12px}.stat strong{font-size:23px}.chart-card{padding:19px 15px}.section-head h2{font-size:23px}.copy-card{padding:20px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.bar rect{transition:none}}
@media print{nav{display:none}.hero{print-color-adjust:exact;-webkit-print-color-adjust:exact}.wrap{max-width:none;padding:0 15px}.panel-grid{grid-template-columns:1fr 1fr}.chart-card,.copy-card{break-inside:avoid;box-shadow:none}.chart-card{padding:15px}.source-list details{display:none}section{margin:25px 0}body{font-size:12px}.stats{gap:10px}}
'''


def _axis_label(value,unit):
    if unit=='percent':return f'{value:.1%}'
    if unit=='USD':return f'${value/1000:,.0f}k' if value>=1000 else f'${value:,.0f}'
    return f'{value:,.0f}'


def _svg(panel,index):
    values=panel['values']; largest=max(values,default=0)
    step=10**floor(log10(largest)) if largest>0 else 1
    maximum=ceil(largest/step)*step or 1
    height=65+len(values)*37; baseline=height-30; left=190; width=355
    title_id=f'chart-title-{index}';desc_id=f'chart-desc-{index}'
    parts=[f'<svg viewBox="0 0 700 {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
        f'<title id="{title_id}">{escape(panel["title"])}</title>',
        f'<desc id="{desc_id}">Horizontal bars start at zero. Values in {escape(panel["unit"])}. '+escape('; '.join(f'{label}: {value_label(value,panel["unit"])}' for label,value in zip(panel['labels'],values)))+'</desc>']
    for i in range(5):
        x=left+width*i/4; tick=maximum*i/4
        parts.extend([f'<line x1="{x}" y1="12" x2="{x}" y2="{baseline}" stroke="#e0e8ed"/>',
            f'<text x="{x}" y="{baseline+21}" text-anchor="middle" font-size="18" fill="#607587">{escape(_axis_label(tick,panel["unit"]))}</text>'])
    for i,(label,value) in enumerate(zip(panel['labels'],values)):
        y=24+i*37; length=width*value/maximum; color='#087f80' if i in panel['highlights'] else '#8ba0af'
        label_text=f'{label}: {value_label(value,panel["unit"])}'
        parts.append(f'<g class="bar" tabindex="0" role="img" aria-label="{escape(label_text,quote=True)}"><title>{escape(label_text)}</title>'
            f'<text x="{left-12}" y="{y+5}" text-anchor="end" font-size="20" fill="#243f54">{escape(label)}</text>'
            f'<rect x="{left}" y="{y-10}" width="{length:.3f}" height="21" rx="3" fill="{color}"/>'
            f'<text x="{left+length+9:.3f}" y="{y+5}" font-size="20" font-weight="700" fill="#10263d">{escape(value_label(value,panel["unit"]))}</text></g>')
    return ''.join(parts)+'</svg>'


def export_html(packet):
    errors=validate_packet(packet)
    if errors:raise ValueError('Report validation failed: '+'; '.join(errors))
    f=packet['facts']; cited=packet['sections'][-1]['citations']; numbers={key:i+1 for i,key in enumerate(cited)}
    def citations(keys):
        return '<div class="citations">Sources: '+', '.join(f'<a href="#source-{numbers[key]}">[{numbers[key]}]</a>' for key in keys)+'</div>'
    def paragraphs(text):return ''.join(f'<p>{escape(p).replace(chr(10),"<br>")}</p>' for p in text.split('\n\n'))
    def head(number,title,ident):return f'<section id="{ident}"><div class="section-head"><span>{number:02d}</span><h2>{escape(title)}</h2></div>'
    def chart(panel,index,svg=True):
        static=_svg(panel,index) if svg else '<p class="chart-note">Exact audience counts are available in the data table below.</p>'
        return ('<figure class="chart-card"><h3>'+escape(panel['title'])+'</h3><div class="chart-unit">'+escape(panel['note'])+'</div>'+
            '<div class="kpi-callout">KPI callout · '+escape(value_label(panel['values'][-1],panel['unit']))+' · '+escape(panel['labels'][-1])+'</div>'+
            f'<div class="interactive-chart" hidden><canvas id="interactive-{index}" role="img" aria-label="'+escape(panel['title'],quote=True)+'"></canvas></div>'+
            '<div class="static-chart">'+static+'</div>'+dashboard.table(panel)+
            '<figcaption class="insight"><h4>'+('What the data shows' if svg else 'What happened')+'</h4><p>'+escape(panel['insight'])+'</p></figcaption>'+
            dashboard.reading(panel)+citations(panel['citations'])+'</figure>')
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{escape(packet["client_name"])} | Campaign Performance Report</title><style>'+dashboard.vendor('bootstrap.min.css')+f'</style><style>{CSS}{dashboard.STYLE}</style></head><body>',
        '<header class="hero"><div class="wrap"><div class="hero-top"><div class="brand">Campaign Intelligence Hub</div><span class="badge">SYNTHETIC DEMONSTRATION DATA</span></div>',
        '<div class="eyebrow">Campaign performance review</div><h1>'+escape(packet['campaign_name'])+'</h1><p class="client">'+escape(packet['client_name'])+'</p>',
        '<div class="hero-meta">'+escape(packet['period'])+' &nbsp; · &nbsp; Data as of '+escape(f['as_of'])+'</div>',
        '<div class="hero-rule"></div><p class="lead">A visual story of goal achievement, channel performance, historical standing and where outcomes originated.</p></div></header>',
        '<nav aria-label="Report sections"><div class="wrap">'+''.join(f'<a href="#{ident}">{label}</a>' for ident,label in [('summary','Overview'),('goals','Goals'),('channels','Channels'),('history','History'),('geography','Geography'),('actions','Actions'),('measurement','Measurement'),('sources','Sources')])+'</div></nav><main class="wrap">',
        dashboard.kpi_cards(packet,citations)]
    parts.extend([head(1,'Executive summary','summary'),'<div class="copy-card">',paragraphs(packet['sections'][0]['text']),citations(packet['sections'][0]['citations']),'</div></section>'])
    families={'Progress Toward Goals':(2,'Goals and achievement','goals'),'Channel performance':(3,'Channel performance','channels'),
        'Same-client historical standing':(4,'Same-client historical standing','history'),'Geographic performance':(5,'Geographic performance','geography')}
    panels=comparison_panels(packet);counter=0
    groups={family:list(items) for family,items in groupby(panels,key=lambda p:p['family'])}
    for family,(number,title,ident) in families.items():
        parts.append(head(number,title,ident))
        if ident=='goals':parts.append('<div class="copy-card">'+paragraphs(packet['sections'][1]['text'])+citations(packet['sections'][1]['citations'])+'</div><br>')
        if ident=='history':parts.append('<p class="section-intro">Earlier campaigns from the same client and product, compared within channel using mature, matching attribution definitions. Teal identifies the current campaign. Small cohorts support descriptive comparisons only.</p>')
        parts.append('<div class="panel-grid">')
        for panel in groups.get(family,[]):
            counter+=1
            legend=('Gray: goal · Teal: actual' if ident=='goals' else 'Gray: prior campaigns · Teal: current campaign' if ident=='history' else 'Teal: largest location' if ident=='geography' else 'Attributed results; no causal lift inferred')
            parts.append(chart({**panel,'note':legend+'. '+panel['note']},counter))
        parts.append('</div>')
        if ident=='history':
            for result in f['history']:
                if result['status']!='ok':parts.append('<div class="callout">No compatible same-client history: '+escape(result['channel'].replace('_',' ').title())+'. No historical rank is inferred.</div>')
            for line in packet['sections'][2]['text'].split('\n\n'):
                if line.startswith('Historical candidates excluded'):parts.append('<div class="callout">'+escape(line)+'</div>')
            missing=packet.get('retrieval',{}).get('unavailable_sources',[])
            if missing:parts.append('<div class="callout">Historical source retrieval unavailable; excluded from available comparisons: '+escape(', '.join(missing))+'.</div>')
            parts.append('<div class="callout">No verified industry benchmark has been supplied. Synthetic cross-client references are not an industry benchmark.</div>')
        parts.append('</section>')
    audience=dashboard.audience_panel(packet)
    if audience:
        panels.append(audience)
    parts.append(dashboard.supplemental(packet,citations,chart(audience,len(panels),svg=False) if audience else '<div class="availability">Audience outcome breakdown unavailable.</div>'))
    parts.extend([head(9,'Learnings and recommended actions','actions'),'<div class="copy-card"><h3>Learnings</h3>',paragraphs(packet['sections'][3]['text']),citations(packet['sections'][3]['citations']),'</div><br><div class="actions">'])
    for section in packet['sections'][4:6]:parts.append('<div class="copy-card"><h3>'+escape(section['title'])+'</h3>'+paragraphs(section['text'])+'<p class="chart-reading"><strong>Expected impact:</strong> Not quantified in the evidence.<br><strong>Priority:</strong> To be agreed; not specified by sources.</p>'+citations(section['citations'])+'</div>')
    parts.extend(['</div></section>',dashboard.storyline(packet,citations),head(11,'Measurement and limitations','measurement'),'<div class="copy-card">',paragraphs(packet['sections'][6]['text']),citations(packet['sections'][6]['citations']),
        '<p class="provenance">Evidence: '+('Chroma retrieval with validated parent-document expansion' if packet.get('evidence_mode')=='rag' else 'Validated source-table snapshot')+'. Source version: '+escape(packet['corpus_hash'])+'</p></div></section>',
        head(12,'Source citations','sources'),'<div class="copy-card"><p class="section-intro">Follow the numbered citations to inspect the source documents behind each chart and finding.</p><ol class="source-list">'])
    for key,number in numbers.items():
        source=packet['sources'][key];meta=source_metadata(source)
        hits=[h['chunk_id'] for h in packet.get('retrieval',{}).get('hits',[]) if h['document_id']==key]
        parts.append(f'<li id="source-{number}"><span class="source-number">[{number}]</span><strong>'+escape(meta['campaign_name'])+'</strong> — '+escape(meta['document_type'].replace('_',' ').title())+
            '<div class="source-meta">'+escape(key)+' · '+escape(meta['client_name'])+' · '+escape(meta['period'])+'</div>'+
            '<details><summary>Read source evidence'+(f' · {len(hits)} retrieved chunks' if hits else '')+'</summary><pre>'+escape(source['text'])+'</pre>'+
            ('<p class="provenance">Retrieved chunk IDs: '+escape(', '.join(hits))+'</p>' if hits else '')+'</details></li>')
    parts.extend(['</ol></div></section></main><footer><div class="wrap">Campaign Intelligence Hub · Prepared for analyst review · Synthetic demonstration data. Charts use validated source values; observations do not establish causal lift or financial ROI.</div></footer>',dashboard.chart_runtime(panels),'</body></html>'])
    return ''.join(parts)
