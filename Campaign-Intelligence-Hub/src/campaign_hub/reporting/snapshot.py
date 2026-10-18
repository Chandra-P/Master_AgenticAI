"""Deterministic source-table retrieval for the live workspace and final reports."""
import hashlib
import json
import re
from decimal import Decimal
import yaml
from campaign_hub.ingestion.markdown import sections
from campaign_hub.reporting.benchmark import parse_channel_results


def source_bundle(service):
    service.ensure_current()
    return {d['document_id']:{'text':(service.settings.data/d['source_path']).read_text(encoding='utf-8'),
        'content_hash':d['content_hash'],'source_path':d['source_path']} for d in service.manifest['documents']}


def source_metadata(source):
    return yaml.safe_load(source['text'].split('---',2)[1])


def chunk_is_in_source(text,source):
    # Fixed chunks use cleaned heading/body joins; semantic chunks retain section bodies.
    cleaned='\n\n'.join(f'## {heading}\n{body}' for heading,body in sections(source['text']))
    return bool(text.strip()) and (text in source['text'] or text in cleaned)


def source_sections(sources,cid,kind):
    key=f'{cid}-{kind}'
    if key not in sources:
        raise ValueError(f'Missing source: {key}')
    return dict(sections(sources[key]['text']))


def snapshot_from_sources(sources,cid):
    src=sources[f'{cid}-performance_report']
    meta=source_metadata(src)
    body=source_sections(sources,cid,'performance_report')
    kpis={}
    schema={'Verified activations':('count','higher'),'Spend':('USD','lower'),
            'Opening account balance':('USD','higher'),'Acquisition cost':('USD/activation','lower')}
    for line in body['KPI Results'].splitlines():
        values=[v.strip() for v in line.strip('|').split('|')]
        if len(values)==6 and values[0] in ('Verified activations','Spend','Opening account balance','Acquisition cost'):
            if values[5]!=meta['period'] or tuple(values[3:5])!=schema[values[0]]:
                raise ValueError('KPI reporting period, unit or direction mismatch')
            if values[0] in kpis:
                raise ValueError('Duplicate KPI row')
            kpis[values[0]]=[Decimal(values[1]),Decimal(values[2])]
    target,actual=kpis['Verified activations']
    budget,spend=kpis['Spend']
    balance_target,balance=kpis['Opening account balance']
    channels=parse_channel_results(body['Channel Results'])
    if set(channels)!={'direct_mail','display'}:
        raise ValueError('Missing or invalid channel attribution data')
    geo=[]
    for line in body['Geographic Results'].splitlines():
        v=[x.strip() for x in line.strip('|').split('|')]
        if len(v)!=8 or v[1] not in channels:
            continue
        geo.append(dict(campaign_id=cid,client_name=meta['client_name'],period=meta['period'],region=meta['region'],
            location=v[0],channel=v[1],accounts=int(v[2]),balance_cents=int(v[3]),exposures=int(v[4]),
            latitude=float(v[5]),longitude=float(v[6]),as_of=v[7]))
    if sum(r['accounts'] for r in geo)!=actual or sum(r['balance_cents'] for r in geo)!=balance*100:
        raise ValueError('Geography does not reconcile to campaign KPIs')
    if sum(c['activations'] for c in channels.values())!=actual or sum(Decimal(str(c['spend'])) for c in channels.values())!=spend:
        raise ValueError('Channel results do not reconcile to campaign KPIs')
    for heading,pattern in [
        ('Performance Drivers',r'Direct mail accounted for (\d+) verified activations and display for (\d+)\.'),
        ('Channel Insights',r'Direct mail: (\d+) activations within 60 days of mail/drop date; display: (\d+) within 30 days of exposure\.')]:
        match=re.match(pattern,body[heading])
        if not match or [int(v) for v in match.groups()]!=[channels['direct_mail']['activations'],channels['display']['activations']]:
            raise ValueError(f'{heading} conflicts with channel results')
    audience=re.match(r'Existing members supplied (\d+) activations and prospective members (\d+);',body['Audience Insights'])
    if not audience or sum(int(v) for v in audience.groups())!=actual:
        raise ValueError('Audience results do not reconcile to total activations')
    if not geo or any(r['accounts']<0 or r['balance_cents']<0 or r['exposures']<=0 or not -90<=r['latitude']<=90 or not -180<=r['longitude']<=180 for r in geo):
        raise ValueError('Invalid geographic measurements')
    for ch,stats in channels.items():
        rows=[r for r in geo if r['channel']==ch]
        if sum(r['accounts'] for r in rows)!=stats['activations'] or sum(r['exposures'] for r in rows)!=stats['exposures'] or any(r['as_of']!=stats['as_of'] for r in rows):
            raise ValueError('Geography/channel reconciliation failed')
    plan=source_sections(sources,cid,'success_plan')
    match=re.fullmatch(r'Verified activations target: (\d+) count; acquisition cost ceiling: USD ([\d.]+)/activation; spend ceiling: USD ([\d.]+); opening account balance target: USD ([\d.]+)\.',plan['Targets'])
    if not match or [Decimal(v) for v in match.groups()]!=[target,kpis['Acquisition cost'][0],budget,balance_target]:
        raise ValueError('Success plan targets conflict with KPI results')
    cost_target,cost_actual=kpis['Acquisition cost']
    if target<=0 or actual<=0 or abs(cost_actual-spend/actual)>Decimal('.011') or abs(cost_target-budget/target)>Decimal('.011'):
        raise ValueError('Acquisition cost arithmetic conflicts with source data')
    return {**meta,'target':int(target),'actual':int(actual),'budget':float(budget),'spend':float(spend),
        'balance_target_cents':int(balance_target*100),'balance_cents':int(balance*100),
        'balance_definition':body['Balance Definition'],'channel_results':channels,'geography':geo,
        'as_of':max(c['as_of'] for c in channels.values())}


def campaign_snapshot(service,cid,client_name=None,channel=None,period=None):
    sources=source_bundle(service)
    snap=snapshot_from_sources(sources,cid)
    if client_name and client_name!=snap['client_name']:
        raise ValueError('Selected client does not own this campaign')
    if channel and channel not in ('direct_mail','display'):
        raise ValueError('Unknown channel')
    raw_geo=json.loads((service.settings.data/'geography.json').read_text(encoding='utf-8'))
    if [r for r in raw_geo if r['campaign_id']==cid]!=snap['geography']:
        raise ValueError('Map dataset conflicts with the cited source table')
    if period and period!=snap['period']:
        return {**snap,'geography':[],'actual':0,'balance_cents':0,'spend':0}
    if channel:
        rows=[r for r in snap['geography'] if r['channel']==channel]
        snap={**snap,'geography':rows,'actual':sum(r['accounts'] for r in rows),
            'balance_cents':sum(r['balance_cents'] for r in rows),'spend':snap['channel_results'][channel]['spend'],
            'target':None,'balance_target_cents':None}
    return snap
