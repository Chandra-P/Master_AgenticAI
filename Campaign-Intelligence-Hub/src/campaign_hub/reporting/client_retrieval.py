"""Metadata-filtered Chroma retrieval followed by validated parent-document expansion."""
from campaign_hub.reporting.snapshot import source_bundle,source_metadata,chunk_is_in_source
from campaign_hub.reporting.client_packet import build_client_packet,validate_packet


def retrieve_client_packet(service,cid,options):
    bundle=source_bundle(service)
    current=service.campaigns[cid]
    requests=[(cid,kind,query) for kind,query in [
        ('brief','Campaign objectives goals audience offer'),
        ('success_plan','Targets KPI Definitions Reporting Window'),
        ('performance_report','KPI Results Channel Results Geographic Results Performance Drivers Audience Insights'),
        ('historical_deck','Recommendations Lessons Learned Suggested Next Steps')]]
    candidates=[c for c in service.campaigns.values() if c['client_name']==current['client_name']
        and c['campaign_type']==current['campaign_type'] and c['period']<current['period']]
    for peer in candidates:
        requests.extend([(peer['campaign_id'],'performance_report','Channel Results KPI Results'),
            (peer['campaign_id'],'success_plan','Targets Reporting Window')])
    requests.append(('GLOBAL','best_practice',current['campaign_type']+' Recommendations tracking controlled tests'))
    selected={}; traces=[]; unavailable=[]
    for campaign,kind,query in requests:
        hits=service.search(query,campaign,options,kind)
        valid=[]
        for hit in hits:
            chunk=hit.chunk; key=chunk.metadata.get('document_id')
            if key not in bundle:
                continue
            parent=bundle[key]; meta=source_metadata(parent)
            if meta['campaign_id']!=campaign or meta['document_type']!=kind:
                continue
            if chunk.metadata.get('content_hash')!=parent['content_hash'] or not chunk_is_in_source(chunk.text,parent):
                raise ValueError('Retrieved chunk differs from its validated parent source')
            valid.append((key,parent,chunk,hit.score))
        if not valid:
            if campaign==cid or campaign=='GLOBAL':
                raise ValueError(f'Retrieval found no validated {kind} evidence for {campaign}; rebuild/check the selected index')
            unavailable.append(f'{campaign}-{kind}')
            continue
        if campaign=='GLOBAL':
            valid.sort(key=lambda r:source_metadata(r[1])['campaign_type']!=current['campaign_type'])
            valid=valid[:1]
        for key,parent,chunk,score in valid:
            selected[key]=parent
            traces.append({'query':query,'document_id':key,'chunk_id':chunk.chunk_id,'chunk_text':chunk.text,
                'score':float(score),'source_hash':parent['content_hash']})
    packet=build_client_packet(service,cid,sources=selected)
    packet['evidence_mode']='rag'
    packet['retrieval']={'options':options.model_dump(),'corpus_hash':service.corpus_hash,'hits':traces,'unavailable_sources':unavailable,
        'expansion':'Retrieved chunks select validated parent documents; calculations use typed source tables.'}
    errors=validate_packet(packet)
    if errors:
        raise ValueError('Retrieved report evidence failed validation: '+'; '.join(errors))
    return packet
