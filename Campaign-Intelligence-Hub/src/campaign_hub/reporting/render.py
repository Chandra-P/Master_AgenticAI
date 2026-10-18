from campaign_hub.models import FALLBACK
import json


def render_report(report):
    text=f'# Campaign Performance Report: {report.campaign_id}\n\nPeriod: {report.period} | Status: {report.status}\n\nSYNTHETIC COURSE DATA\n\n'
    text+=f'Evidence coverage score: {report.confidence:.0%} (heuristic, not probability of correctness).\n\n'
    ids=list(report.evidence)
    for section in report.sections:
        text+='## '+section.title+'\n\n'
        if section.title=='Source Citations':
            for cid,chunk in report.evidence.items():
                text+=f"- [{ids.index(cid)+1}] {chunk.metadata['source_path']}#{chunk.metadata.get('section_anchor','')} — {chunk.metadata.get('section_name','')}\n"
        else:
            text+='\n\n'.join(c.text+' '+''.join(f'[{ids.index(cid)+1}]' for cid in c.citations if cid in ids) for c in section.claims)
            if section.gap or not section.claims:
                text+='\n\n'+(section.gap or FALLBACK)
        text+='\n\n'
    text+='## Report provenance and input coverage\n\n```json\n'+json.dumps(report.provenance,indent=2)+'\n```\n'
    return text
