"""Opt-in question-based context focus; never reads evaluation labels or references."""
import re


def context_plan(question):
    lower=question.lower()
    if re.search(r'\b(compar\w*|histor\w*|earlier|achiev\w*|track\w*|perform\w*|versus|vs|met|meet)\b',lower):
        return None,[]
    if re.search(r'\b(objectives?|goals?)\b',lower) and not re.search(r'\b(actual|results?|perform\w*)\b',lower):
        # A single goal section cannot answer compound requests such as goals and audience.
        if re.search(r'\b(and|also|plus|as well|along with)\b',lower):
            return None,[]
        metric=bool(re.search(r'\b(balances?|cost|spend|budget|rates?|revenue|deposits?|activations?|conversions?|kpis?|roi|channels?|display|mail)\b',lower))
        return ('success_plan',['Targets']) if metric else ('brief',['Objectives'])
    if re.search(r'\b(results?|actuals?)\b',lower) and re.search(r'\bchannels?\b',lower):
        return 'performance_report',['KPI Results','Channel Insights']
    return None,[]


def focus_context(question,hits):
    from campaign_hub.reporting.service import section_evidence
    _,headings=context_plan(question)
    if not headings:return hits
    selected=[];seen=set()
    for hit in hits:
        for heading in headings:
            chunk=section_evidence(hit.chunk,heading)
            if chunk and chunk.chunk_id not in seen:
                selected.append(hit.model_copy(update={'chunk':chunk}))
                seen.add(chunk.chunk_id)
    # Never drop a requested section merely because its candidate was not retrieved.
    if {h.chunk.metadata.get('section_name') for h in selected}>=set(headings):
        return selected
    return hits
