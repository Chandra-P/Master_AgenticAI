"""Four matched retrieval experiments; never invent generation scores."""
from pathlib import Path
import json,math,time,statistics,os

def retrieval_metrics(ranked:list[str],relevant:list[str])->dict:
    relevant=set(relevant);ranked=list(dict.fromkeys(ranked))[:5]
    if not relevant:return {'recall_at_5':None,'reciprocal_rank':None,'ndcg_at_5':None}
    gains=[int(x in relevant) for x in ranked]
    recall=len(set(ranked)&relevant)/len(relevant)
    rr=next((1/(i+1) for i,g in enumerate(gains) if g),0)
    dcg=sum(g/math.log2(i+2) for i,g in enumerate(gains))
    ideal=sum(1/math.log2(i+2) for i in range(min(5,len(relevant))))
    return {'recall_at_5':recall,'reciprocal_rank':rr,'ndcg_at_5':dcg/ideal}

def questions():
    def case(i,q,charter,kind,row):
        return {'id':f'Q{i:02}','question':q,'filters':{'charter':charter,'year_2025':True},
                'relevant':[f'{charter}-{kind}-2025.html|{row}'],'expected':'source_evidence'}
    cases=[
      case(1,'What were Navy Federal total assets in December 2025?','5536','summary','TOTAL ASSETS'),
      case(2,'How did Navy Federal total loans change from 2023 through 2025?','5536','summary','TOTAL LOANS'),
      case(3,'What was Navy Federal delinquent loans divided by assets in 2025?','5536','historical','Delinquent Loans / Assets'),
      case(4,'What was Pentagon total equity in 2025?','227','summary','TOTAL EQUITY'),
      case(5,'What was Boeing Employees total shares and deposits in 2025?','62604','summary','TOTAL SHARES & DEPOSITS'),
      case(6,'How did Alliant total assets change between 2023 and 2025?','67955','summary','TOTAL ASSETS'),
      case(7,'What was First Technology total loans in 2025?','19976','summary','TOTAL LOANS'),
      case(8,'What were Spokane Firefighters total assets in 2025?','68205','summary','TOTAL ASSETS'),
      case(9,'What were State Employees total investments in 2025?','66310','summary','TOTAL INVESTMENTS'),
      case(10,'How did America First total loans change from 2023 to 2025?','24694','summary','TOTAL LOANS'),
      case(11,'What was Mountain America delinquent loans divided by assets in 2025?','24692','historical','Delinquent Loans / Assets'),
      {'id':'Q12','question':'Compare Navy Federal and Pentagon total assets in 2025.','filters':{'year_2025':True},
       'relevant':['5536-summary-2025.html|TOTAL ASSETS','227-summary-2025.html|TOTAL ASSETS'],'expected':'cross_document'},
      {'id':'Q13','question':'What were Navy Federal total assets in 2030?','filters':{},'relevant':[],'expected':'abstain'},
      {'id':'Q14','question':'What is the CEO home address?','filters':{},'relevant':[],'expected':'abstain'},
      {'id':'Q15','question':'What are total assets for charter 99999 in 2025?','filters':{'charter':'99999'},'relevant':[],'expected':'abstain'}]
    return cases

def evaluate(root:Path,embedder=None)->dict:
    from .index import Store,LocalEmbeddings,RERANKER_REVISION
    from .retrieve import retrieve
    from sentence_transformers import CrossEncoder
    root=Path(root);dest=root/'evaluation';dest.mkdir(exist_ok=True)
    cases=questions();(dest/'questions.json').write_text(json.dumps(cases,indent=2))
    embedder=embedder or LocalEmbeddings()
    reranker=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2',revision=RERANKER_REVISION,local_files_only=os.getenv('HF_HUB_OFFLINE')=='1')
    results=[]
    for strategy in ('fixed','semantic'):
        store=Store(root/'data/chroma',strategy,embedder)
        for rerank in (False,True):
            rows=[]
            for case in cases:
                start=time.perf_counter();found=retrieve(store,case['question'],case['filters'],reranker if rerank else None)
                elapsed=time.perf_counter()-start
                keys=[]
                for d in found:
                    labels=d.metadata.get('rows',d.metadata.get('row','')).split(' | ')
                    keys.extend(d.metadata['source']+'|'+label for label in labels)
                # Relevance is attributed per returned chunk; multi-row chunks count once.
                seen=set();ranked=[]
                for d in found:
                    labels=d.metadata.get('rows',d.metadata.get('row','')).split(' | ')
                    hits=[d.metadata['source']+'|'+label for label in labels if d.metadata['source']+'|'+label in case['relevant']]
                    key=next((h for h in hits if h not in seen),d.id)
                    ranked.append(key);seen.add(key)
                metrics=retrieval_metrics(ranked,case['relevant'])
                row={**case,**metrics,'seconds':elapsed,'abstained':not found,'retrieved_chunk_ids':[d.id for d in found],
                     'retrieved':[{'text':d.page_content,**d.metadata} for d in found]}
                rows.append(row)
            positives=[r for r in rows if r['relevant']];negatives=[r for r in rows if not r['relevant']]
            summary={metric:statistics.mean(r[metric] for r in positives) for metric in ('recall_at_5','reciprocal_rank','ndcg_at_5')}
            timings=sorted(r['seconds'] for r in rows)
            summary.update(abstention_accuracy=statistics.mean(r['abstained'] for r in negatives),p95_retrieval_seconds=timings[math.ceil(.95*len(timings))-1])
            result={'strategy':strategy,'rerank':rerank,'summary':summary,'queries':rows};results.append(result)
            print(strategy,'rerank',rerank,summary,flush=True)
    report={'results':results,'embedding_model':getattr(embedder,'identity','external'),'reranker':'cross-encoder/ms-marco-MiniLM-L-6-v2',
            'generation_metrics':{'faithfulness':None,'answer_relevance':None,'reason':'Retrieval-only experiment; see generation-results.json for separate live responses.'},
            'timing_scope':'Local warm retrieval only; excludes remote network and answer generation.',
            'labels':'Expected table rows manually selected from the downloaded original NCUA reports before scoring.'}
    (dest/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Chunking and reranking comparison','','Measured on the same 15 questions and source corpus. Twelve evidence questions and three expected abstentions.','',
           '| Chunking | Rerank | Recall@5 | MRR | nDCG@5 | Abstention | Retrieval p95 (s) |','|---|---|---:|---:|---:|---:|---:|']
    for r in results:
        s=r['summary'];lines.append(f"| {r['strategy']} | {r['rerank']} | {s['recall_at_5']:.3f} | {s['reciprocal_rank']:.3f} | {s['ndcg_at_5']:.3f} | {s['abstention_accuracy']:.3f} | {s['p95_retrieval_seconds']:.3f} |")
    lines+=['','## Measured reranking impact']
    for strategy in ('fixed','semantic'):
        a,b=[r for r in results if r['strategy']==strategy]
        lines.append(f"- {strategy}: recall@5 delta {b['summary']['recall_at_5']-a['summary']['recall_at_5']:+.3f}; MRR delta {b['summary']['reciprocal_rank']-a['summary']['reciprocal_rank']:+.3f}.")
    lines+=['','## Failure analysis']
    for r in results:
        failed=[x['id'] for x in r['queries'] if (x['relevant'] and x['recall_at_5']<1) or (not x['relevant'] and not x['abstained'])]
        lines.append(f"- {r['strategy']}, rerank={r['rerank']}: incomplete or incorrect retrieval on {', '.join(failed) or 'none of these cases'}. Inspect raw results for context.")
    lines+=['','An institution filter makes single-institution questions easier. The cross-document case intentionally has no institution filter; five passages can miss one institution or the required financial row. Similar table labels and repeated institution headers can dominate similarity. Semantic chunks may combine adjacent rows; larger chunks can improve coverage while diluting precision.',
            '', '## Limits and targets','Recall@5 target: 0.80. Faithfulness target: 0.90. End-to-end warm p95 target: 15 seconds. This experiment measures retrieval only. See generation-results.json for the separate live generation assessment. Public load performance is unmeasured. Retrieval metrics are not answer accuracy. Negative cases use explicit evidence gates; they do not establish general hallucination resistance.',
            '', 'For multi-row chunks, nDCG/MRR use one new relevant row per retrieved chunk; recall follows the ranked chunk relevance mapping. Labels are source rows, not answer text. This small hand-labeled evaluation is a learning demonstration, not a statistically representative benchmark.']
    (dest/'comparison-report.md').write_text('\n'.join(lines),encoding='utf8')
    return report
