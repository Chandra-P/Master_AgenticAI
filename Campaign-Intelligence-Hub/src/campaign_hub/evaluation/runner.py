import itertools
import json
import time
import hashlib
from pathlib import Path
from campaign_hub.models import RetrievalOptions, FALLBACK
from campaign_hub.evaluation.metrics import retrieval_metrics, citation_accuracy
from campaign_hub.reporting.render import render_report


def configurations():
    return [RetrievalOptions(chunking=c,retrieval=r,reranking=k) for c,r,k in itertools.product(['fixed','semantic'],['dense','hybrid'],[False,True])]


def completeness(answer,facts):
    return sum(str(f).lower() in answer.lower() for f in facts)/len(facts) if facts else None


def run_experiments(service,output,smoke=False,use_llm=True,judge=False):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    cases=json.loads((service.settings.data/'evaluation/questions.json').read_text())
    cases=[c for c in cases if c['split']=='held_out']
    if smoke:
        cases=cases[:1]
    rows=[]
    for options in configurations():
        for case in cases:
            identity={'options':options.model_dump(),'question':case['id'],'corpus':service.corpus_hash,
                      'embedding':service.settings.embedding_model,'generation':service.settings.generation_model,'use_llm':use_llm,'judge':judge,'runner_version':2}
            key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
            path=output/(key+'.json')
            if path.exists():
                rows.append(json.loads(path.read_text()))
                continue
            started=time.perf_counter()
            row={**options.model_dump(),'case_id':case['id'],'identity':identity,'faithfulness':None,
                 'faithfulness_note':'No independent entailment judge run; score unavailable.', 'error':None}
            try:
                cited=[]
                claims=[]
                evidence={}
                if case['kind']=='report':
                    period=service.campaigns[case['campaign_id']]['period']
                    report=service.generate_report(case['campaign_id'],period,options,use_llm=use_llm)
                    answer=render_report(report)
                    docs=[c.metadata['document_id'] for c in report.evidence.values()]
                    row['section_coverage']=report.confidence
                    row['report_status']=report.status
                    claims=[c for s in report.sections for c in s.claims]
                    evidence=report.evidence
                elif use_llm:
                    result=service.answer_question(case['question'],case['campaign_id'],options)
                    answer=result['answer']
                    docs=[h['chunk']['metadata']['document_id'] for h in result['hits']]
                    from campaign_hub.models import Chunk,EvidenceClaim
                    evidence={h['chunk']['chunk_id']:Chunk.model_validate(h['chunk']) for h in result['hits']}
                    claims=[EvidenceClaim.model_validate(c) for c in result.get('claims',[])]
                else:
                    hits=service.search(case['question'],case['campaign_id'],options) if case['campaign_id'] in service.campaigns else []
                    docs=[h.chunk.metadata['document_id'] for h in hits]
                    answer='\n'.join(h.chunk.text for h in hits)
                    row['generation_skipped']=True
                row.update(retrieval_metrics(docs,case['expected_sources']))
                for claim in claims:
                    for cid in claim.citations:
                        if cid in evidence:
                            meta=evidence[cid].metadata
                            cited.append(meta['document_id']+'#'+meta['section_anchor'])
                row['citation_accuracy']=citation_accuracy(cited,case['ground_truth_citations'])
                row['citation_metric_note']='Gold source/section overlap; not entailment accuracy.'
                if judge and claims:
                    from campaign_hub.evaluation.judge import judge_claims
                    from campaign_hub.generation.providers import OllamaGenerator
                    row.update(judge_claims(claims,evidence,OllamaGenerator(service.settings)))
                    row['judge_model']=service.settings.generation_model
                row['answer_completeness']=completeness(answer,case['expected_facts'])
                row['abstention_accuracy']=float(answer==FALLBACK) if case['kind']=='unsupported' and use_llm else None
                row['answer']=answer
                row['retrieved_documents']=docs
            except Exception as error:
                row['error']=str(error)
            row['latency_seconds']=time.perf_counter()-started
            path.write_text(json.dumps(row,indent=2),encoding='utf-8')
            rows.append(row)
    (output/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    import pandas as pd
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in rows]).to_csv(output/'results.csv',index=False)
    return rows
