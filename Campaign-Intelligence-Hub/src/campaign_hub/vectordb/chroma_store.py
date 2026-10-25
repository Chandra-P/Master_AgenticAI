import json
import hashlib
from pathlib import Path
from importlib.metadata import version
import chromadb
from langchain_chroma import Chroma
from campaign_hub.models import Chunk, SearchHit
from campaign_hub.retrieval.filters import chroma_where


def default_chunking_config(strategy='section'):
    from campaign_hub.chunking.pipeline import STRATEGIES
    if strategy not in STRATEGIES:raise ValueError('Unknown chunking strategy')
    config={'tokenizer':'cl100k_base','tokenizer_version':version('tiktoken'),
            'window':500,'overlap':50,'pipeline_version':2,'strategy':strategy,
            'algorithm':{'fixed':'token_windows','section':'markdown_sections','semantic':'sentence_cosine_percentile'}[strategy]}
    if strategy=='semantic':
        config.update(semantic_percentile=65,unit_version=1,table_protection=True)
    return config


class ChromaStore:
    def __init__(self, root: Path, strategy: str, embedder, chunking_config=None):
        self.root = Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.embedder = embedder
        self.strategy = strategy
        self.chunking_config=chunking_config or default_chunking_config(strategy)
        identity = hashlib.sha256(json.dumps({'embedder':embedder.identity,'chunker':self.chunking_config},sort_keys=True).encode()).hexdigest()[:12]
        self.name = f'campaign-{strategy}-{identity}'
        self.client = chromadb.PersistentClient(path=str(root))
        self.manifest_path = self.root / (self.name+'.json')
        self.collection = self.client.get_or_create_collection(self.name, metadata={'hnsw:space':'cosine'})
        self.vectorstore=Chroma(client=self.client,collection_name=self.name,embedding_function=embedder)

    def assert_compatible(self, corpus_hash):
        if not self.manifest_path.exists():
            raise ValueError('Index missing; rebuild the selected index')
        meta = json.loads(self.manifest_path.read_text())
        if (meta['corpus_hash'] != corpus_hash or meta['embedder'] != self.embedder.identity
                or meta.get('chunking_config') != self.chunking_config
                or (self.embedder.identity.get('dimensions') is not None and meta['dimensions'] != self.embedder.identity['dimensions'])):
            raise ValueError('Index incompatible; rebuild the selected index')

    def build(self, chunks, corpus_hash):
        if not chunks:
            raise ValueError('Cannot index an empty corpus')
        for chunk in chunks:
            meta=chunk.metadata
            if meta.get('chunking',self.strategy)!=self.strategy:
                raise ValueError('Chunking configuration differs from the index strategy')
            if self.strategy=='semantic' and 'semantic_percentile' in meta:
                if (meta['semantic_percentile']!=self.chunking_config['semantic_percentile']
                    or json.loads(meta['segmentation_embedder'])!=self.embedder.identity):
                    raise ValueError('Semantic chunking configuration differs from the index')
        desired = {c.chunk_id for c in chunks}
        current = self.collection.get()['ids']
        stale = [cid for cid in current if cid not in desired]
        if stale:
            self.collection.delete(ids=stale)
        dimensions = None
        for start in range(0,len(chunks),32):
            batch = chunks[start:start+32]
            vectors = self.embedder.embed_documents([c.text for c in batch])
            dimensions = len(vectors[0])
            self.collection.upsert(ids=[c.chunk_id for c in batch], documents=[c.text for c in batch],
                embeddings=vectors, metadatas=[c.metadata for c in batch])
        self.manifest_path.write_text(json.dumps({'corpus_hash':corpus_hash,'embedder':self.embedder.identity,
            'dimensions':dimensions,'count':len(chunks),'strategy':self.strategy,'chunking_config':self.chunking_config},indent=2))

    def search(self, query, filters=None, k=20):
        if not self.collection.count():
            return []
        filters = filters or {}
        where = chroma_where(filters)
        result=self.vectorstore.similarity_search_with_score(query,k=min(k,self.collection.count()),filter=where or None)
        return [SearchHit(chunk=Chunk(chunk_id=doc.id,text=doc.page_content,metadata=doc.metadata),score=1-distance,dense_score=1-distance)
                for doc,distance in result]

    def chunks(self, filters=None):
        filters = filters or {}
        where = chroma_where(filters)
        data = self.collection.get(where=where or None)
        return [Chunk(chunk_id=i,text=t,metadata=m) for i,t,m in zip(data['ids'],data['documents'],data['metadatas'])]
