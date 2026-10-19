"""Resolve source references without inventing section anchors for whole documents."""
import re
from campaign_hub.ingestion.markdown import anchor


def source_anchors(chunk):
    anchors=chunk.metadata.get('section_anchors','').split('|')
    anchors=[a for a in anchors if a and a!='document']
    if not anchors:
        single=chunk.metadata.get('section_anchor','')
        anchors=[single] if single and single!='document' else []
    return list(dict.fromkeys(anchors))


def source_references(chunk):
    path=chunk.metadata['source_path']
    return [path+'#'+a for a in source_anchors(chunk)] or [path]


def claim_section(text,chunk):
    """Return one unambiguous section; unknown spans remain unscored."""
    single=chunk.metadata.get('section_anchor','')
    if single and single!='document':
        return single
    if not text:
        return None
    headings=list(re.finditer(r'^## (.+)$',chunk.text,re.M))
    spans=[]
    if headings and headings[0].start()>0:
        # Overlapping-anchor metadata does not locate a leading partial section.
        spans.append((0,headings[0].start(),None))
    spans.extend((h.start(),headings[i+1].start() if i+1<len(headings) else len(chunk.text),anchor(h.group(1)))
                 for i,h in enumerate(headings))
    matches=list(re.finditer(re.escape(text),chunk.text))
    resolved=[]
    for match in matches:
        section=next((name for start,end,name in spans if start<=match.start() and match.end()<=end),None)
        if section is None:
            return None
        resolved.append(section)
    return resolved[0] if resolved and len(set(resolved))==1 else None
