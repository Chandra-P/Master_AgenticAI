"""Hybrid retrieval with LangChain Documents and optional cross-encoder reranking."""
import math,re
from collections import Counter

def tokens(text):return re.findall(r'[a-z0-9]+',text.lower())

def bm25(question,documents):
    if not documents:return []
    query=set(tokens(question));bags=[Counter(tokens(d.page_content)) for d in documents]
    avg=sum(sum(b.values()) for b in bags)/len(bags);scores=[]
    for d,b in zip(documents,bags):
        total=0.;length=sum(b.values())
        for term in query:
            n=sum(term in x for x in bags);idf=math.log(1+(len(bags)-n+.5)/(n+.5))
            f=b[term];total+=idf*f*2.5/(f+1.5*(.25+.75*length/max(avg,1)))
        if total>0:scores.append((d,total))
    return [d for d,_ in sorted(scores,key=lambda x:(-x[1],x[0].id))]

def wants_annual(question):
    q=question.lower()
    if any(x in q for x in ('ratio',' / ','per member','potential member')):return False
    return 'annual report' in q or bool(re.search(r'\b(member|members|membership)\b',q))

def select_documents(question,documents):
    q=question.lower()
    annual=wants_annual(question)
    selected=[d for d in documents if (d.metadata.get('source_type')=='institution_annual_report')==annual]
    if annual:
        requested=set(re.findall(r'\b20\d{2}\b',q))
        if len(requested)==2 and re.search(r'\b(to|through|between)\b',q):requested={str(y) for y in range(int(min(requested)),int(max(requested))+1)}
        if requested:selected=[d for d in selected if str(d.metadata.get('report_year')) in requested]
    return selected

def retrieve(store,question,filters=None,reranker=None,k=5):
    filters=dict(filters or {})
    requested=set(re.findall(r'\b20\d{2}\b',question))
    if requested-set(str(y) for y in range(2021,2026)):return []
    # Reject absent topics rather than forcing every query through nearest neighbors.
    if not set(tokens(question)) & {'asset','assets','loan','loans','delinquency','delinquent','growth','income','equity','capital','cash','investment','investments','shares','deposits','borrowings','liabilities','ratio','ratios','member','members','membership','annual','credit','union'}:return []
    annual=wants_annual(question)
    if annual and requested:filters={k:v for k,v in filters.items() if not k.startswith('year_')}
    documents=select_documents(question,store.all_documents(filters))
    if not documents:return []
    selected_ids={d.id for d in documents}
    rankings=[[d for d in store.search(question,filters,k=60) if d.id in selected_ids][:20],bm25(question,documents)[:20]]
    scores={};lookup={}
    for ranking in rankings:
        for rank,d in enumerate(ranking,start=1):
            scores[d.id]=scores.get(d.id,0)+1/(60+rank);lookup[d.id]=d
    candidates=[lookup[i] for i in sorted(scores,key=lambda x:(-scores[x],x))[:20]]
    if reranker is not None and candidates:
        relevance=reranker.predict([(question,d.page_content) for d in candidates])
        candidates=[d for d,_ in sorted(zip(candidates,relevance),key=lambda x:-float(x[1]))]
    return candidates[:k]
