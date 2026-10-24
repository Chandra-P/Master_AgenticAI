"""Source-frozen retrieval comparison; no Groq calls or model tuning."""
from pathlib import Path
import json,re,hashlib,time,statistics,random,math,os
ROOT=Path(__file__).resolve().parents[1]
def compact(text):return re.sub(r'[\s,$]','',text.casefold())
def anchor_match(anchor,text):
    canonical=lambda t:re.sub(r'\s+',' ',re.sub(r'[,$]','',t.casefold())).strip()
    value=canonical(anchor);pattern=re.escape(value).replace(r'\ ',r'\s*')
    return bool(re.search(r'(?<![\d.])'+pattern+(r'(?!\d)' if value[-1:].isdigit() else ''),canonical(text)))
def score_hits(hits,keys):
    if not keys:return {'recall_at_5':None,'reciprocal_rank':None}
    covered=set().union(*(set(h) for h in hits[:5])) if hits else set()
    return {'recall_at_5':len(covered.intersection(keys))/len(set(keys)),
            'reciprocal_rank':next((1/(i+1) for i,h in enumerate(hits[:5]) if set(h).intersection(keys)),0)}
def hits_for(document,units):
    meta=document.metadata;rows=meta.get('rows',meta.get('row','')).split(' | ')
    return [u['key'] for u in units if meta['source']==u['source'] and
            ((u['kind']=='row' and u['row'] in rows) or
             (u['kind']=='pdf_anchor' and meta.get('pdf_page') in u.get('accepted_pages',[u['page']]) and any(anchor_match(a,document.page_content) for a in u.get('anchor_variants',[u['anchor']]))))]
def summarize(rows):
    positive=[r for r in rows if r['gold_units']];negative=[r for r in rows if not r['gold_units']]
    times=sorted(r['seconds'] for r in rows)
    return {'evidence_questions':len(positive),'negative_questions':len(negative),
            'recall_at_5':statistics.mean(r['recall_at_5'] for r in positive) if positive else None,
            'reciprocal_rank':statistics.mean(r['reciprocal_rank'] for r in positive) if positive else None,
            'abstention_accuracy':statistics.mean(r['abstained'] for r in negative) if negative else None,
            'p95_retrieval_seconds':times[math.ceil(.95*len(times))-1]}
def paired(fixed,semantic,metric):
    other={r['id']:r for r in semantic};diff=[other[r['id']][metric]-r[metric] for r in fixed if r['gold_units']]
    rng=random.Random(20261019);draws=sorted(statistics.mean(rng.choices(diff,k=len(diff))) for _ in range(2000))
    return {'mean_semantic_minus_fixed':statistics.mean(diff),'bootstrap_95_ci':[draws[49],draws[1949]],
            'semantic_wins':sum(d>1e-10 for d in diff),'ties':sum(abs(d)<=1e-10 for d in diff),'fixed_wins':sum(d< -1e-10 for d in diff)}
def run():
    Path('outputs').mkdir(exist_ok=True)
    from pipeline.index import Store,LocalEmbeddings,RERANKER_REVISION
    from pipeline.retrieve import retrieve
    from sentence_transformers import CrossEncoder
    directory=ROOT/'evaluation/expanded';label_path=directory/'questions.json';label_bytes=label_path.read_bytes()
    plan=json.loads(label_bytes);cases=plan['cases'];label_hash=hashlib.sha256(label_bytes).hexdigest()
    embedder=LocalEmbeddings();reranker=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2',revision=RERANKER_REVISION,local_files_only=True)
    stores={s:Store(ROOT/'data/chroma',s,embedder) for s in ('fixed','semantic')}
    configs=[(s,r) for s in stores for r in (False,True)]
    rows={str(c):[] for c in configs}
    print('Loaded frozen labels and both indexes; warming models.',flush=True)
    for strategy,rerank in configs:retrieve(stores[strategy],cases[0]['question'],cases[0]['filters'],reranker if rerank else None)
    rng=random.Random(20261019);order=list(cases);rng.shuffle(order)
    for i,case in enumerate(order,1):
        config_order=list(configs);rng.shuffle(config_order)
        for strategy,rerank in config_order:
            start=time.perf_counter();found=retrieve(stores[strategy],case['question'],case['filters'],reranker if rerank else None)
            elapsed=time.perf_counter()-start;hits=[hits_for(d,case['gold_units']) for d in found]
            row={**case,**score_hits(hits,[u['key'] for u in case['gold_units']]),'seconds':elapsed,'abstained':not found,'ranked_evidence_hits':hits,
                 'retrieved':[{'chunk_id':d.id,'text':d.page_content,**d.metadata} for d in found]}
            rows[str((strategy,rerank))].append(row)
        print(f'{i}/{len(cases)} {case["id"]} complete',flush=True)
        (directory/'checkpoint.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    results=[]
    for strategy,rerank in configs:
        current=sorted(rows[str((strategy,rerank))],key=lambda r:r['id']);groups={domain:summarize([r for r in current if r['domain']==domain]) for domain in ('ncua','annual')}
        results.append({'strategy':strategy,'rerank':rerank,'summary':summarize(current),'by_domain':groups,
                        'source_balanced':{metric:statistics.mean(groups[d][metric] for d in groups) for metric in ('recall_at_5','reciprocal_rank')},'queries':current})
    comparisons=[]
    for rerank in (False,True):
        f,s=[r for r in results if r['rerank']==rerank]
        comparisons.append({'rerank':rerank,**{metric:paired(f['queries'],s['queries'],metric) for metric in ('recall_at_5','reciprocal_rank')}})
    assert label_path.read_bytes()==label_bytes
    report={'cases':len(cases),'positive_questions':32,'negative_questions':6,'label_sha256':label_hash,'results':results,'paired_comparisons':comparisons,
            'corpus':{'ncua_reports':19,'annual_reports':10,'fixed_chunks':stores['fixed'].collection.count(),'semantic_chunks':stores['semantic'].collection.count()},
            'label_method':plan['label_method'],'timing_scope':'Local warmed retrieval only; randomized configuration order within shuffled questions. No generation, network or UI latency.',
            'limits':'Exploratory, manually labeled convenience set. Questions share reports and institutions, so question-bootstrap intervals can overstate certainty. Not a held-out general benchmark. All evidence units in a retrieved passage count toward recall; MRR uses first matching passage. nDCG omitted because multi-fact passages require a separately specified gain model. No tuning or question selection after results.'}
    (directory/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Expanded corpus: fixed versus semantic chunking','','38 pre-labeled questions: original 15 NCUA cases, 20 annual-report evidence questions and 3 annual-report missing-evidence cases. All four configurations use the same 29 documents and frozen questions.','','## Combined results (32 evidence questions, 6 negatives)','','| Chunker | Rerank | Recall@5 | MRR | Abstention | Retrieval p95 (s) |','|---|---|---:|---:|---:|---:|']
    for result in results:
        t=result['summary'];lines.append(f"| {result['strategy']} | {result['rerank']} | {t['recall_at_5']:.3f} | {t['reciprocal_rank']:.3f} | {t['abstention_accuracy']:.3f} | {t['p95_retrieval_seconds']:.3f} |")
    for domain in ('ncua','annual'):
        lines+=['',f'## {domain.upper()} questions','','| Chunker | Rerank | Recall@5 | MRR | Abstention |','|---|---|---:|---:|---:|']
        for result in results:
            t=result['by_domain'][domain];lines.append(f"| {result['strategy']} | {result['rerank']} | {t['recall_at_5']:.3f} | {t['reciprocal_rank']:.3f} | {t['abstention_accuracy']:.3f} |")
    lines+=['','## Source-balanced comparison','','Each source domain receives 50% weight, rather than allowing the 20 annual evidence questions to outweigh the 12 NCUA evidence questions.','','| Chunker | Rerank | Balanced recall | Balanced MRR |','|---|---|---:|---:|']
    for result in results:
        t=result['source_balanced'];lines.append(f"| {result['strategy']} | {result['rerank']} | {t['recall_at_5']:.3f} | {t['reciprocal_rank']:.3f} |")
    lines+=['','## Paired differences (semantic minus fixed)']
    for comparison in comparisons:
        for metric in ('recall_at_5','reciprocal_rank'):
            t=comparison[metric];lines.append(f"- Rerank {comparison['rerank']}, {metric}: mean {t['mean_semantic_minus_fixed']:+.3f}; exploratory 95% bootstrap interval [{t['bootstrap_95_ci'][0]:+.3f}, {t['bootstrap_95_ci'][1]:+.3f}]; semantic wins/ties/fixed wins: {t['semantic_wins']}/{t['ties']}/{t['fixed_wins']}.")
    lines+=['','## Coverage and limitations',report['limits'],'',report['timing_scope'],'','BECU 2023 is image-only in this extraction; BECU 2024 contains mostly captions. No OCR was added. These and the absent Alliant annual report are explicit missing-evidence cases. Abstention here means empty retrieval, not a generated-answer faithfulness judgment.','',f'Frozen label SHA-256: {label_hash}']
    text='\n'.join(lines);(directory/'comparison-report.md').write_text(text,encoding='utf8')
    Path('outputs/expanded-chunking-evaluation.md').write_text(text,encoding='utf8')
    Path('outputs/expanded-chunking-results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    for result in results:print(result['strategy'],result['rerank'],result['summary'],flush=True)
    print('PAIRED',json.dumps(comparisons),flush=True)
if __name__=='__main__':run()
