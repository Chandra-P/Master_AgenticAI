"""LangChain Chroma persistence and MiniLM embeddings."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json, os
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma
import chromadb
EMBEDDING_REVISION='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
RERANKER_REVISION='233902d25c440f23af6f7d6e94d2946bac0bee0a'

class LocalEmbeddings(Embeddings):
    def __init__(self,model='sentence-transformers/all-MiniLM-L6-v2'):
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(model,revision=EMBEDDING_REVISION if model=='sentence-transformers/all-MiniLM-L6-v2' else None,local_files_only=os.getenv('HF_HUB_OFFLINE')=='1')
        self.model.max_seq_length=256
        self.identity=model
        self.tokenizer=self.model.tokenizer
    def embed_documents(self,texts):
        return self.model.encode(texts,normalize_embeddings=True,batch_size=32,show_progress_bar=False).tolist()
    def embed_query(self,text):return self.embed_documents([text])[0]

def where_filter(filters:dict)->dict|None:
    allowed={'charter','year_2021','year_2022','year_2023','year_2024','year_2025'}
    if any(k not in allowed for k in filters):raise ValueError('Unsupported metadata filter')
    if not filters:return None
    return {'$and':[{k:v} for k,v in filters.items()]} if len(filters)>1 else filters

class Store:
    def __init__(self,root:Path,strategy:str,embedder:Embeddings,cloud:bool=False):
        if strategy not in ('fixed','semantic'):raise ValueError('Unknown chunking strategy')
        self.embedder=embedder;self.strategy=strategy;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        identity=sha256(str(getattr(embedder,'identity','external')).encode()).hexdigest()[:8]
        self.name=f'ncua-{strategy}-v1-{identity}'
        self.client=chromadb.CloudClient() if cloud else chromadb.PersistentClient(path=str(self.root))
        self.collection=self.client.get_or_create_collection(self.name,metadata={'hnsw:space':'cosine'})
        self.vectorstore=Chroma(client=self.client,collection_name=self.name,embedding_function=embedder)
    def build(self,documents:list[Document])->None:
        if not documents:raise ValueError('Refusing to replace corpus with an empty index')
        digest=sha256(json.dumps([(d.id,d.page_content,d.metadata) for d in documents],sort_keys=True).encode()).hexdigest()
        manifest=self.root/(self.name+'.json')
        if manifest.exists() and json.loads(manifest.read_text()).get('hash')==digest and self.collection.count()==len(documents):return
        desired={d.id for d in documents}
        existing=self.collection.get(include=['documents','metadatas'])
        previous={key:(text,meta) for key,text,meta in zip(existing['ids'],existing['documents'],existing['metadatas'])}
        stale=[key for key in previous if key not in desired]
        pending=[d for d in documents if previous.get(d.id)!=(d.page_content,d.metadata)]
        # Upsert before deleting so a failed embedding batch does not erase the old corpus.
        for offset in range(0,len(pending),32):
            batch=pending[offset:offset+32]
            self.vectorstore.add_documents(batch,ids=[d.id for d in batch])
        if stale:self.collection.delete(ids=stale)
        manifest.write_text(json.dumps({'hash':digest,'count':len(documents),'model':getattr(self.embedder,'identity','external'),'strategy':self.strategy},indent=2))
    def search(self,query:str,filters:dict|None=None,k:int=20)->list[Document]:
        if not self.collection.count():return []
        return self.vectorstore.similarity_search(query,k=min(k,self.collection.count()),filter=where_filter(filters or {}))
    def all_documents(self,filters:dict|None=None)->list[Document]:
        r=self.collection.get(where=where_filter(filters or {}),include=['documents','metadatas'])
        return [Document(id=i,page_content=t,metadata=m) for i,t,m in zip(r['ids'],r['documents'],r['metadatas'])]

def build_index(data:Path,index:Path,embedder=None):
    from .extract import load_documents
    from .chunk import fixed_chunks,semantic_chunks
    embedder=embedder or LocalEmbeddings();documents=load_documents(data);result={}
    for strategy,fn in [('fixed',fixed_chunks),('semantic',semantic_chunks)]:
        chunks=fn(documents,tokenizer=embedder.tokenizer) if strategy=='fixed' else fn(documents,embedder,tokenizer=embedder.tokenizer)
        s=Store(index,strategy,embedder);s.build(chunks);result[strategy]={'collection':s.name,'chunks':len(chunks)}
        print(strategy,len(chunks),'chunks',flush=True)
    (Path(index)/'collections.json').write_text(json.dumps(result,indent=2))
    return result
