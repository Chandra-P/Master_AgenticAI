from functools import lru_cache


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import CrossEncoder
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def rerank(query,hits):
    if not hits:
        return []
    try:
        scores=model().predict([(query,h.chunk.text) for h in hits])
    except Exception as error:
        raise RuntimeError(f'Cross-encoder unavailable; download the model or explicitly disable reranking: {error}') from error
    for hit,score in zip(hits,scores):
        hit.rerank_score=float(score)
    return sorted(hits,key=lambda h:-h.rerank_score)
