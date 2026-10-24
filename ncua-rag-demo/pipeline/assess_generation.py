"""Collect live responses on the same labeled questions for manual faithfulness review."""
from pathlib import Path
import json,time
from datetime import datetime,timezone
import requests
from dotenv import dotenv_values

def collect(root:Path,base_url='http://127.0.0.1:8765')->dict:
    root=Path(root);env=dotenv_values(root/'.env');header={'Authorization':'Bearer '+env.get('RAG_BACKEND_TOKEN','')}
    questions=json.loads((root/'evaluation/questions.json').read_text());rows=[]
    destination=root/'evaluation/generation-results.json'
    report={'model':env.get('GROQ_MODEL'),'provider':'Groq','strategy':'fixed','rerank':True,
            'assessed_at':datetime.now(timezone.utc).isoformat(),'questions':rows,
            'faithfulness':None,'answer_relevance':None,'assessment_method':'Collected live responses; semantic claim support requires a separate manual review.'}
    for i,case in enumerate(questions):
        filters=case.get('filters',{});years=[k[5:] for k,v in filters.items() if k.startswith('year_') and v]
        payload={'question':case['question'],'charter':filters.get('charter',''),'year':years[0] if years else '',
                 'strategy':'fixed','rerank':True}
        start=time.perf_counter()
        r=requests.post(base_url+'/api/ask',json=payload,headers=header,timeout=60)
        result=r.json();rows.append({'id':case['id'],'question':case['question'],'expected':case['expected'],
                                    'http_status':r.status_code,'client_seconds':time.perf_counter()-start,**result})
        destination.write_text(json.dumps(report,indent=2),encoding='utf8')
        print(case['id'],result.get('status',result.get('error')),flush=True)
        if i<len(questions)-1:time.sleep(12)
    return report

if __name__=='__main__':collect(Path(__file__).resolve().parent.parent)
