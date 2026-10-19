import re
from rank_bm25 import BM25Okapi
from campaign_hub.models import SearchHit


def words(text):
    return re.findall(r'[a-z0-9]+',text.lower())


def fuse(dense, lexical):
    scores, objects = {}, {}
    for hits in [dense,lexical]:
        for rank, hit in enumerate(hits,1):
            cid = hit.chunk.chunk_id
            scores[cid] = scores.get(cid,0)+1/(60+rank)
            objects.setdefault(cid,hit.model_copy(deep=True))
            if hit.bm25_score is not None:
                objects[cid].bm25_score=hit.bm25_score
    for cid in objects:
        objects[cid].score=scores[cid]
    return sorted(objects.values(),key=lambda h:(-h.score,h.chunk.chunk_id))


def retrieve(store, query, filters, options):
    dense = store.search(query,filters,options.candidate_k)
    if options.retrieval=='dense':
        candidates=dense
    else:
        chunks=store.chunks(filters)
        if not chunks:
            return []
        bm25=BM25Okapi([words(c.text) or ['empty'] for c in chunks])
        scores=bm25.get_scores(words(query))
        # Cached stores can outlive a Streamlit module reload. Revalidate plain
        # data instead of requiring the cached Pydantic class's identity.
        lexical=[SearchHit(chunk=chunks[i].model_dump(),score=float(scores[i]),bm25_score=float(scores[i])) for i in sorted(range(len(chunks)),key=lambda i:-scores[i])[:options.candidate_k]]
        candidates=fuse(dense,lexical)[:options.candidate_k]
    if options.reranking:
        from campaign_hub.reranking.cross_encoder import rerank
        candidates=rerank(query,candidates)
    return candidates[:options.final_k]
