"""Two reproducible chunkers over the same extracted source rows."""
from hashlib import sha256
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _identified(doc:Document,text:str,strategy:str,part:int)->Document:
    meta={**doc.metadata,'strategy':strategy,'part':part}
    key=f"{meta['source']}|{meta.get('row_number','')}|{strategy}|{part}|{text}"
    return Document(id=sha256(key.encode()).hexdigest()[:24],page_content=text,metadata=meta)

def fixed_chunks(documents:list[Document],size:int=200,overlap:int=30,tokenizer=None)->list[Document]:
    if size<=0 or overlap<0 or overlap>=size:raise ValueError('Invalid chunk size/overlap')
    if tokenizer is not None:
        splitter=RecursiveCharacterTextSplitter.from_huggingface_tokenizer(tokenizer,chunk_size=size,chunk_overlap=overlap)
    else:
        splitter=RecursiveCharacterTextSplitter(chunk_size=size,chunk_overlap=overlap,length_function=lambda s:len(s.split()))
    return [_identified(d,t,'fixed',i) for d in documents for i,t in enumerate(splitter.split_text(d.page_content))]

def semantic_chunks(documents:list[Document],encoder,size:int=200,tokenizer=None)->list[Document]:
    # Split any single oversized row first, so neither strategy silently truncates a table.
    units=fixed_chunks(documents,size=size,overlap=0,tokenizer=tokenizer)
    if not units:return []
    vectors=np.asarray(encoder.embed_documents([d.page_content for d in units]),dtype=float)
    vectors/=np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
    count=lambda s:len(tokenizer.encode(s,add_special_tokens=False)) if tokenizer else len(s.split())
    out=[];group=[];texts=[];current=None
    def flush():
        if not group:return
        base=group[0];meta={**base.metadata,'rows':' | '.join(d.metadata.get('row','') for d in group),
                           'row_numbers':','.join(str(d.metadata.get('row_number','')) for d in group)}
        out.append(_identified(Document(page_content='',metadata=meta),'\n\n'.join(texts),'semantic',len(out)))
    for i,d in enumerate(units):
        same=current is None or (d.metadata['source'],d.metadata.get('section'),d.metadata.get('pdf_page'))==(current.metadata['source'],current.metadata.get('section'),current.metadata.get('pdf_page'))
        similarity=1.0 if i==0 else float(vectors[i]@vectors[i-1])
        combined='\n\n'.join(texts+[d.page_content])
        if group and (not same or similarity<0.55 or count(combined)>size):
            flush();group=[];texts=[]
        group.append(d);texts.append(d.page_content);current=d
    flush()
    return out
