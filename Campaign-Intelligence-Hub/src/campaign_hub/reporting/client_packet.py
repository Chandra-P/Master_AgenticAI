"""Validated, deterministic client narrative. Model-generated prose is never published here."""
import hashlib
from campaign_hub.reporting.snapshot import source_bundle,source_sections,source_metadata,snapshot_from_sources,chunk_is_in_source
from campaign_hub.reporting.benchmark import compare_campaign
from campaign_hub.ingestion.markdown import sections as document_sections


def _compose(sources,cid):
    current=snapshot_from_sources(sources,cid)
    for kind in ('brief','success_plan','historical_deck'):
        meta=source_metadata(sources[f'{cid}-{kind}'])
        if any(meta[k]!=current[k] for k in ('campaign_id','client_name','campaign_name','period')):
            raise ValueError('Linked source identity mismatch')
    records=[current]
    excluded=[]
    for source in sources.values():
        meta=source_metadata(source)
        if (meta['document_type']!='performance_report' or meta['campaign_id']==cid
                or meta['campaign_type']!=current['campaign_type'] or meta['period']>=current['period']):
            continue
        try:
            records.append(snapshot_from_sources(sources,meta['campaign_id']))
        except (KeyError,ValueError,ZeroDivisionError) as error:
            excluded.append(meta['campaign_id'])
    history=[compare_campaign(current,records,ch) for ch in ('direct_mail','display')]
    references=[compare_campaign(current,records,ch,scope='peer_reference') for ch in ('direct_mail','display')]
    facts={k:current[k] for k in ('target','actual','budget','spend','balance_target_cents','balance_cents','balance_definition',
        'channel_results','geography','as_of','client_name','campaign_name','period','campaign_id')}
    facts['history']=history
    facts['peer_reference']=references
    p=f'{cid}-performance_report'; brief=f'{cid}-brief'; plan=f'{cid}-success_plan'; deck=f'{cid}-historical_deck'
    performance=source_sections(sources,cid,'performance_report')
    historical=source_sections(sources,cid,'historical_deck')
    sections=[]
    def add(title,text,citations):
        sections.append({'title':title,'text':text,'citations':list(dict.fromkeys(citations))})
    attainment=current['actual']/current['target']*100
    add('Executive Summary',f"{current['actual']} verified activations against a goal of {current['target']} ({attainment:.1f}% attainment). "
        f"The activation goal was {'met' if attainment>=100 else 'not met'}. Spend was USD {current['spend']:,.2f} against a USD {current['budget']:,.2f} ceiling. "
        f"Opening account balances totaled USD {current['balance_cents']/100:,.2f} as of {current['as_of']}. "
        'These are attributed outcomes; causal lift and ROI were not measured.',[p,plan])
    add('Goals',source_sections(sources,cid,'brief')['Objectives']+'\n\n'+source_sections(sources,cid,'success_plan')['Targets'],[brief,plan])
    progress=[f"Activations: {current['actual']} / {current['target']} ({attainment:.1f}%). Variance: {current['actual']-current['target']:+d}.",
        f"Spend: USD {current['spend']:,.2f} / USD {current['budget']:,.2f}; {'within' if current['spend']<=current['budget'] else 'above'} budget.",
        f"Acquisition cost: USD {current['spend']/current['actual']:.2f} per activation; ceiling USD {current['budget']/current['target']:.2f}.",
        f"Opening balances: USD {current['balance_cents']/100:,.2f} / USD {current['balance_target_cents']/100:,.2f} target."]
    for ch,s in current['channel_results'].items():
        cost=f"USD {s['spend']/s['activations']:.2f}" if s['activations'] else 'unavailable (zero activations)'
        progress.append(f"{ch.replace('_',' ').title()}: {s['activations']} activations from {s['exposures']} {s['exposure_unit'].replace('_',' ')} "
            f"({s['activations']/s['exposures']:.2%}); {cost} per activation. "
            f"Attribution: {s['window_days']} days from {s['anchor'].replace('_',' ')}; as of {s['as_of']}.")
    history_citations=[]
    for result in history:
        if result['status']!='ok':
            progress.append(f"{result['channel']}: insufficient comparable same-client historical evidence.")
            continue
        for metric,m in result['metrics'].items():
            fmt=lambda n:f'{n:.2%}' if metric=='activation_rate' else f'USD {n:.2f}'
            progress.append(f"Same-client history, {result['channel']}, {metric.replace('_',' ')}: {fmt(m['current'])} vs median {fmt(m['peer_median'])}; "
                f"rank {m['rank']} of {m['total']} including this campaign, {m['position']}. Comparable earlier campaigns: {m['peer_count']}.")
        progress.append('Small cohort: descriptive comparison only; no population or statistical significance claim.')
        history_citations.extend(f'{peer}-performance_report' for peer in result['peer_ids'])
    progress.append('Industry benchmark: unavailable. Synthetic cross-client references are not an industry benchmark.')
    if excluded:
        progress.append('Historical candidates excluded because source tables failed validation: '+', '.join(excluded)+'.')
    top=max(current['geography'],key=lambda r:r['accounts'])
    progress.append(f"Largest location/channel cell by accounts: {top['location']} / {top['channel']}, {top['accounts']} accounts and USD {top['balance_cents']/100:,.2f} opening balances. See the geographic table for all cells.")
    add('Progress Toward Goals','\n\n'.join(progress),[p,plan]+history_citations)
    add('Learnings','Performance drivers: '+performance['Performance Drivers']+'\n\nAudience: '+performance['Audience Insights']+
        '\n\nChannels: '+performance['Channel Insights']+'\n\nLessons: '+historical['Lessons Learned'],[p,deck])
    guides=[(key,s) for key,s in sources.items() if source_metadata(s)['document_type']=='best_practice']
    if not guides:
        raise ValueError('Missing best practice evidence')
    guide_key,guide=next(((key,s) for key,s in guides if source_metadata(s)['campaign_type']==current['campaign_type']),guides[0])
    guidance=dict(document_sections(guide['text']))['Recommendations'].split('\n\n')[0]
    add('Recommendations','Proposed tests, not proven performance improvements: '+historical['Recommendations']+'\n\nBest-practice guidance: '+guidance,[deck,guide_key])
    add('Suggested Next Steps',historical['Suggested Next Steps']+
        '\n\nProposed action owners: unassigned. Priority and due dates: to be agreed with the client; no source specifies them.',[deck])
    add('Measurement Notes and Limitations',current['balance_definition']+'\n\n'+performance['Measurement Limitations']+
        '\n\n'+source_sections(sources,cid,'success_plan')['Reporting Window']+
        '\n\nMap locations are fictional aggregated outcomes at approximate city centers, not customer addresses. '
        'Rates use channel-specific denominators and must not be compared as causal channel lift. '
        'All institutions, data and findings in this demonstration are synthetic.',[p,plan])
    cited=list(dict.fromkeys(c for s in sections for c in s['citations']))
    add('Source Citations','\n'.join(f"[{i+1}] {source_metadata(sources[key])['campaign_name']} | {source_metadata(sources[key])['document_type'].replace('_',' ')} | {key}" for i,key in enumerate(cited)),cited)
    blockers=[]
    if not all(s['mature'] for s in current['channel_results'].values()):
        blockers.append('Attribution windows are not fully observed.')
    warnings=['Synthetic demonstration data.','Historical cohorts are small; descriptive comparison only.','No verified industry benchmark supplied.']
    return facts,sections,{'ready':not blockers,'blockers':blockers,'warnings':warnings}


def build_client_packet(service,cid,sources=None):
    sources=source_bundle(service) if sources is None else sources
    # Retain campaign documents only; every calculation can be reproduced from this frozen bundle.
    sources={key:s for key,s in sources.items() if source_metadata(s)['campaign_id']!='GLOBAL' or source_metadata(s)['document_type']=='best_practice'}
    facts,sections,readiness=_compose(sources,cid)
    return {'schema_version':2,'evidence_mode':'source_table','campaign_id':cid,'client_name':facts['client_name'],'campaign_name':facts['campaign_name'],
        'period':facts['period'],'corpus_hash':service.corpus_hash,'facts':facts,'sections':sections,'sources':sources,'readiness':readiness}


def validate_packet(packet):
    errors=[]
    try:
        for key,s in packet['sources'].items():
            if hashlib.sha256(s['text'].encode()).hexdigest()!=s['content_hash']:
                errors.append(f'Source changed: {key}')
        if packet.get('evidence_mode')=='rag':
            retrieval=packet['retrieval']
            if retrieval['corpus_hash']!=packet['corpus_hash']:
                errors.append('Retrieval corpus version mismatch.')
            retrieved=set()
            for hit in retrieval['hits']:
                parent=packet['sources'][hit['document_id']]
                if not hit['chunk_id'] or hit['source_hash']!=parent['content_hash'] or not chunk_is_in_source(hit['chunk_text'],parent):
                    errors.append('Invalid retrieved chunk attribution.')
                retrieved.add(hit['document_id'])
            if not set(packet['sources'])<=retrieved:
                errors.append('Report sources lack retrieved chunk evidence.')
        facts,sections,readiness=_compose(packet['sources'],packet['campaign_id'])
        if facts!=packet['facts']:
            errors.append('Facts fail source reconciliation.')
        if sections!=packet['sections']:
            errors.append('Narrative or citations differ from the validated factual rendering.')
        if any(packet[k]!=facts[k] for k in ('client_name','campaign_name','period')):
            errors.append('Report cover identity differs from source identity.')
        if not readiness['ready'] or not packet['readiness']['ready']:
            errors.append('Report is not ready: attribution or validation failed.')
    except (KeyError,ValueError,TypeError,ZeroDivisionError) as exc:
        errors.append(f'Missing or invalid evidence: {exc}')
    return errors


def packet_markdown(packet):
    errors=validate_packet(packet)
    if errors:
        raise ValueError('Report validation failed: '+'; '.join(errors))
    text=f"# Campaign Performance Report\n\n{packet['client_name']}\n\n{packet['campaign_name']} | {packet['period']}\n\nSYNTHETIC DEMONSTRATION DATA\n"
    for section in packet['sections']:
        text+=f"\n## {section['title']}\n\n{section['text']}\n\n"+' '.join(f'[{c}]' for c in section['citations'])+'\n'
    return text
