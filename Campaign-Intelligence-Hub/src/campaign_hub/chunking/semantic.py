"""Embedding-driven topic boundaries with exact source spans and protected tables."""
import re
import numpy as np


def units(text):
    """Sentence spans; a contiguous Markdown table remains one semantic unit."""
    result=[]
    for block in re.finditer(r'\S[\s\S]*?(?=\n\s*\n|\Z)',text):
        value=block.group()
        if any(line.lstrip().startswith('|') for line in value.splitlines()):
            result.append((block.start(),block.end()))
            continue
        start=block.start()
        for split in re.finditer(r'(?<=[.!?])\s+(?=[A-Z0-9])',value):
            end=block.start()+split.start()
            result.append((start,end));start=block.start()+split.end()
        if start<block.end():result.append((start,block.end()))
    return result


def embedding_matrix(values,count):
    try:
        vectors=np.asarray(values,dtype=float)
        if vectors.ndim!=2 or vectors.shape[0]!=count or not vectors.shape[1]:raise ValueError()
        with np.errstate(over='ignore',invalid='ignore'):
            norms=np.linalg.norm(vectors,axis=1)
        if not np.isfinite(vectors).all() or not np.isfinite(norms).all() or np.any(norms==0):raise ValueError()
    except (TypeError,ValueError) as error:
        raise ValueError('Invalid semantic embedding response') from error
    return vectors


def semantic_spans(text,embedder,percentile=65,*,vectors=None):
    if embedder is None:raise ValueError('Semantic chunking requires an embedder')
    if not 0<=percentile<=100:raise ValueError('Semantic percentile must be between 0 and 100')
    spans=units(text)
    if not spans:return []
    if len(spans)==1:return [(spans[0][0],spans[0][1],'document_end',0.0)]
    vectors=embedding_matrix(vectors if vectors is not None else embedder.embed_documents([text[a:b] for a,b in spans]),len(spans))
    norms=np.linalg.norm(vectors,axis=1)
    normalized=vectors/norms[:,None]
    distances=np.clip(1-np.sum(normalized[:-1]*normalized[1:],axis=1),0,2)
    threshold=float(np.percentile(distances,percentile))
    result=[];start=spans[0][0]
    for i,distance in enumerate(distances):
        # Strict comparison prevents arbitrary splits when all distances tie.
        if distance>threshold+1e-12:
            result.append((start,spans[i][1],'semantic',threshold))
            start=spans[i+1][0]
    result.append((start,spans[-1][1],'document_end',threshold))
    return result


def bounded_spans(text,encoder,window=500,overlap=50):
    """Token-bounded windows cut on character boundaries, preserving Unicode."""
    encoded=encoder.encode(text)
    if not encoded:return
    _,offsets=encoder.decode_with_offsets(encoded)
    offsets.append(len(text));start=0
    while start<len(encoded):
        end=min(start+window,len(encoded))
        while end>start and len(encoder.encode(text[offsets[start]:offsets[end]]))>window:
            end-=1
        if end<=start or offsets[end]<=offsets[start]:
            raise ValueError('Cannot form a token-safe source span')
        yield offsets[start],offsets[end],end<len(encoded)
        if end==len(encoded):break
        start=max(start+1,end-overlap)
