"""Narrow factual answers from retrieved sections and count tables, never gold data."""
import re
from campaign_hub.ingestion.markdown import sections

VERSION=1


def _scope(hits):
    scopes={(h.chunk.metadata.get('campaign_id'),h.chunk.metadata.get('period')) for h in hits}
    if len(scopes)!=1:
        return False
    campaign,period=next(iter(scopes))
    return bool(campaign and campaign!='GLOBAL' and period and period!='ALL')


def _result(claims,proof,method):
    return {'answer':'\n\n'.join(c['text']+' '+''.join('['+i+']' for i in c['citations']) for c in claims),
            'claims':claims,'accepted_claims':len(claims),'draft_claims':0,
            'evidence_method':method,'source_proof':proof,'faithfulness':None}


def _tables(text):
    lines=text.splitlines();index=0
    while index+1<len(lines):
        line=lines[index].strip();separator=lines[index+1].strip()
        if not line.startswith('|') or not re.fullmatch(r'[| :\-]+',separator) or '-' not in separator:
            index+=1;continue
        headers=[c.strip().lower() for c in line.strip('|').split('|')]
        index+=2
        while index<len(lines) and lines[index].strip().startswith('|'):
            raw=lines[index].strip();cells=[c.strip() for c in raw.strip('|').split('|')]
            if len(cells)==len(headers):yield dict(zip(headers,cells)),raw,line
            index+=1


def _number(value):
    return int(value.replace(',','')) if re.fullmatch(r'(?:0|[1-9]\d*|[1-9]\d{0,2}(?:,\d{3})+)',value) else None


def _complete_objective(settings,chunk,text):
    """Verify completeness without adding facts absent from the retrieved quote."""
    import hashlib
    from pathlib import Path
    root=getattr(settings,'data',None)
    if not isinstance(root,Path):return False
    path=(root/chunk.metadata.get('source_path','')).resolve()
    if not path.is_relative_to((root/'corpus').resolve()) or not path.is_file():return False
    original=path.read_text(encoding='utf-8')
    if hashlib.sha256(original.encode()).hexdigest()!=chunk.metadata.get('content_hash'):return False
    return dict(sections(original)).get('Objectives')==text


def factual_answer(question,hits,settings=None):
    """Return None unless one narrow intent has complete, consistent source support."""
    if not hits or not _scope(hits):return None
    lower=re.sub(r'\s+',' ',question.lower()).strip(' ?.!')
    prefix=r'(?:(?:what (?:are|were)|summarize) (?:the )?)?'
    suffix=r'(?: (?:for|of|about) (?:campaign )?([a-z0-9]+(?:-[a-z0-9]+)+))?'
    objective=re.fullmatch(prefix+r'(?:objectives?|goals?)'+suffix,lower)
    counts=re.fullmatch(prefix+r'(?:results?|actuals?) (?:and channel (?:findings|results|breakdown)|by channel)'+suffix,lower)
    match=objective or counts
    if match is None:return None
    requested_campaign=match.group(1)
    if requested_campaign and any(h.chunk.metadata['campaign_id'].lower()!=requested_campaign for h in hits):return None
    if objective:
        candidates={}
        for hit in hits:
            chunk=hit.chunk
            if chunk.metadata.get('document_type')!='brief':continue
            parts=dict(sections(chunk.text))
            text=parts.get('Objectives')
            if text is None and chunk.metadata.get('section_name')=='Objectives':
                text=chunk.text.strip()
            if text and _complete_objective(settings,chunk,text.strip()):
                candidates.setdefault(text.strip(),chunk.chunk_id)
        if len(candidates)==1:
            text,cid=next(iter(candidates.items()))
            return _result([{'text':text,'citations':[cid]}],[{'source_id':cid,'quote':text}], 'retrieved_objective_extract')
        return None
    totals={};channels={};proof=[]
    for hit in hits:
        chunk=hit.chunk
        if chunk.metadata.get('document_type')!='performance_report':continue
        for row,raw,header in _tables(chunk.text):
            if row.get('period') and row['period']!=chunk.metadata.get('period'):return None
            if row.get('metric','').lower()=='verified activations' and row.get('unit','').lower()=='count' and 'actual' in row:
                value=_number(row['actual'])
                if value is None:return None
                totals.setdefault(value,chunk.chunk_id)
                proof.append({'source_id':chunk.chunk_id,'header':header,'row':raw,'column':'actual','value':value})
            if 'channel' in row and 'activations' in row:
                label=row['channel'].lower().replace('_',' ').replace('-',' ')
                if not re.fullmatch(r'[a-z][a-z ]{0,49}',label):return None
                value=_number(row['activations'])
                if value is None:return None
                values=channels.setdefault(label,{})
                values.setdefault(value,chunk.chunk_id)
                proof.append({'source_id':chunk.chunk_id,'header':header,'row':raw,'column':'activations','value':value})
    if len(totals)!=1 or not channels or any(len(values)!=1 for values in channels.values()):return None
    total,total_id=next(iter(totals.items()))
    if sum(next(iter(values)) for values in channels.values())!=total:return None
    claims=[{'text':str(total)+' activations.','citations':[total_id]}]
    for label,values in channels.items():
        value,cid=next(iter(values.items()))
        claims.append({'text':label.capitalize()+': '+str(value)+' activations.','citations':[cid]})
    return _result(claims,proof,'retrieved_table_projection')
