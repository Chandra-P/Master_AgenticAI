import hashlib
import json
import re
import tiktoken
from campaign_hub.models import Chunk
from campaign_hub.ingestion.markdown import sections, anchor


def tokens(text):
    return tiktoken.get_encoding('cl100k_base').encode(text)


STRATEGIES=('fixed','section','semantic')
LABELS={'fixed':'Fixed-size','section':'Section-based','semantic':'Embedding-based semantic'}


def chunk_documents(documents, strategy='section', *, embedder=None, semantic_percentile=65):
    if strategy not in STRATEGIES:
        raise ValueError('Unknown chunking strategy')
    if strategy=='semantic' and embedder is None:
        raise ValueError('Semantic chunking requires an embedder')
    from campaign_hub.chunking.semantic import semantic_spans,bounded_spans,units,embedding_matrix
    encoder = tiktoken.get_encoding('cl100k_base')
    result = [];prepared=[]
    for doc in documents:
        parts = list(sections(doc.text))
        cleaned='\n\n'.join(f'## {h}\n{b}' for h,b in parts) if parts else doc.text.strip()
        prepared.append((doc,parts,cleaned))
    vectors_by_document={}
    if strategy=='semantic':
        if not 0<=semantic_percentile<=100:raise ValueError('Semantic percentile must be between 0 and 100')
        texts=[];ranges={}
        for i,(_,_,cleaned) in enumerate(prepared):
            spans=units(cleaned)
            if len(spans)>1:
                start=len(texts);texts.extend(cleaned[a:b] for a,b in spans)
                ranges[i]=(start,len(texts))
        if texts:
            vectors=embedding_matrix(embedder.embed_documents(texts),len(texts))
            vectors_by_document={i:vectors[a:b] for i,(a,b) in ranges.items()}
    for i,(doc,parts,cleaned) in enumerate(prepared):
        if strategy=='semantic':
            headings=list(re.finditer(r'^## (.+)$',cleaned,re.M))
            for begin,end,reason,threshold in semantic_spans(cleaned,embedder,semantic_percentile,vectors=vectors_by_document.get(i)):
                for a,b,overflow in bounded_spans(cleaned[begin:end],encoder):
                    start,stop=begin+a,begin+b;text=cleaned[start:stop]
                    names=[m.group(1) for i,m in enumerate(headings)
                        if m.start()<stop and (headings[i+1].start() if i+1<len(headings) else len(cleaned))>start]
                    heading=names[0] if len(names)==1 else 'Document'
                    content_hash=hashlib.sha256(text.encode()).hexdigest()
                    result.append(Chunk(chunk_id=f"{doc.metadata['document_id']}:semantic:{start}:{content_hash[:8]}",text=text,
                        metadata={**doc.metadata,'section_name':heading,'section_anchor':anchor(heading),
                            'section_anchors':'|'.join(anchor(n) for n in names) or 'document',
                            'token_count':len(tokens(text)),'chunking':'semantic','tokenizer':'cl100k_base',
                            'chunk_hash':content_hash,'char_start':start,'char_end':stop,
                            'boundary_reason':'token_limit' if overflow else reason,'semantic_threshold':threshold,
                            'semantic_percentile':semantic_percentile,'chunker_version':2,
                            'segmentation_embedder':json.dumps(embedder.identity,sort_keys=True)}))
            continue
        groups = (parts or [('Document',cleaned)]) if strategy == 'section' else [('Document',cleaned)]
        for heading, body in groups:
            for start,end,overflow in bounded_spans(body,encoder):
                text = body[start:end]
                # Fixed chunks may span sections; keep all matching anchors for audit.
                names = [h for h,b in parts if h in text or (text[:40].strip() and text[:40].strip() in b)] if strategy=='fixed' else [heading]
                if not names:
                    names = [heading]
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                cid = f"{doc.metadata['document_id']}:{strategy}:{anchor(heading)}:{start}:{content_hash[:8]}"
                result.append(Chunk(chunk_id=cid, text=text, metadata={**doc.metadata, 'section_name': heading,
                    'section_anchor': anchor(heading), 'section_anchors': '|'.join(anchor(n) for n in names),
                    'token_count': len(tokens(text)), 'chunking': strategy, 'tokenizer': 'cl100k_base', 'chunk_hash':content_hash}))
    return result
