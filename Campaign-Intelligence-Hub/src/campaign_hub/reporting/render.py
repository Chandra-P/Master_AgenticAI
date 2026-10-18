from campaign_hub.models import FALLBACK,ReportResult
import json


def enrich_report_identity(report,campaign):
    data=report if isinstance(report,dict) else report.model_dump()
    normalized=ReportResult.model_validate(data)
    return normalized.model_copy(update={'client_name':campaign.get('client_name',''),
                                         'campaign_name':campaign.get('campaign_name','')})


def render_report(report,client_facing=False):
    text=f'# Campaign Performance Report: {report.campaign_id}\n\n'
    if report.client_name:
        text+=f'**Client:** {report.client_name}\n\n'
    if report.campaign_name:
        text+=f'**Campaign:** {report.campaign_name}\n\n'
    text+=f'**Reporting period:** {report.period} | **Report status:** {report.status}\n\nSYNTHETIC COURSE DATA — fictional demonstration; not actual client results.\n\n'
    text+=f'Evidence coverage score: {report.confidence:.0%} (heuristic, not probability of correctness).\n\n'
    ids=list(report.evidence)
    for section in report.sections:
        text+='## '+section.title+'\n\n'
        if section.title=='Source Citations':
            for cid,chunk in report.evidence.items():
                if client_facing:
                    name=chunk.metadata.get('campaign_name','Campaign evidence')
                    kind=chunk.metadata.get('document_type','Source document').replace('_',' ').title()
                    section=chunk.metadata.get('section_name','')
                    text+=f"- [{ids.index(cid)+1}] {name} — {kind}: {section}\n"
                else:
                    text+=f"- [{ids.index(cid)+1}] {chunk.metadata['source_path']}#{chunk.metadata.get('section_anchor','')} — {chunk.metadata.get('section_name','')}\n"
        else:
            text+='\n\n'.join(c.text+' '+''.join(f'[{ids.index(cid)+1}]' for cid in c.citations if cid in ids) for c in section.claims)
            if section.gap or not section.claims:
                text+='\n\n'+(section.gap or FALLBACK)
        text+='\n\n'
    if not client_facing:
        text+='## Report provenance and input coverage\n\n```json\n'+json.dumps(report.provenance,indent=2)+'\n```\n'
    return text.rstrip()+'\n'
