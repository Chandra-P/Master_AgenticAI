"""Ollama embeddings with bounded batches and content-addressed local cache."""
import hashlib
import json
from functools import lru_cache
from threading import RLock
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings


class OllamaEmbedder(Embeddings):
    def __init__(self, settings):
        self.settings = settings
        self.client=OllamaEmbeddings(model=settings.embedding_model,base_url=settings.ollama_url,
                                     client_kwargs={'timeout':180})
        self.identity = {'provider':'langchain-ollama', 'model':settings.embedding_model, 'normalization':'embeddinggemma-query-document-v1'}
        self.cache = settings.data / 'cache/embeddings'
        self.cache.mkdir(parents=True, exist_ok=True)

    def _embed(self, texts):
        output = [None]*len(texts)
        missing = []
        for i, text in enumerate(texts):
            key = hashlib.sha256((json.dumps(self.identity,sort_keys=True)+text).encode()).hexdigest()
            path = self.cache / (key+'.json')
            if path.exists():
                output[i] = json.loads(path.read_text())
            else:
                missing.append((i,text,path))
        for start in range(0,len(missing),16):
            batch = missing[start:start+16]
            try:
                vectors = self.client.embed_documents([x[1] for x in batch])
            except Exception as error:
                raise RuntimeError(f'Ollama embedding failed. Start Ollama and run: ollama pull {self.settings.embedding_model}. {error}') from error
            if len(vectors) != len(batch) or not vectors or not vectors[0]:
                raise ValueError('Invalid embedding response')
            for (i,_,path), vector in zip(batch,vectors):
                output[i] = vector
                path.write_text(json.dumps(vector))
        if output and len({len(v) for v in output}) != 1:
            raise ValueError('Embedding dimensions changed; clear cache and rebuild')
        return output

    def embed_documents(self, texts):
        formatted = ['title: Campaign evidence | text: '+t if 'embeddinggemma' in self.settings.embedding_model else t for t in texts]
        return self._embed(formatted)

    def embed_query(self, text):
        if 'embeddinggemma' in self.settings.embedding_model:
            text = 'task: search result | query: '+text
        return self._embed([text])[0]


_CPU_LOCK=RLock()


@lru_cache(maxsize=1)
def _sentence_model(name):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name,device='cpu',trust_remote_code=False)


def _token_windows(model,text):
    """Use the encoder's tokenizer budget, not the course chunker's token count."""
    tokenizer=model.tokenizer
    budget=model.max_seq_length-tokenizer.num_special_tokens_to_add(pair=False)
    if budget<2:raise ValueError('Embedding model token budget is too small')
    encoded=tokenizer(text,add_special_tokens=False,truncation=False,return_offsets_mapping=True)
    offsets=encoded['offset_mapping'];total=len(encoded['input_ids'])
    if not total:return [(text,1)]
    overlap=min(32,max(1,budget//4));windows=[];start=0;covered=0
    while start<total:
        end=min(start+budget,total)
        while end>start:
            value=text[offsets[start][0]:offsets[end-1][1]]
            if len(tokenizer(value,add_special_tokens=False,truncation=False)['input_ids'])<=budget:break
            end-=1
        if end<=start:raise ValueError('Cannot construct a model-safe embedding window')
        windows.append((value,max(1,end-covered)));covered=max(covered,end)
        if end==total:break
        start=max(start+1,end-overlap)
    return windows


class SentenceTransformerEmbedder(Embeddings):
    """Server-side CPU embeddings; visitors need no model service or credentials."""
    def __init__(self,settings):
        self.settings=settings
        self.identity={'provider':'sentence-transformers','model':settings.embedding_model,
            'normalization':'model-token-windows-weighted-mean-l2-v2'}
        self.cache=settings.data/'cache/embeddings'
        self.cache.mkdir(parents=True,exist_ok=True)

    def embed_documents(self,texts):
        with _CPU_LOCK:
            result=[None]*len(texts);missing=[]
            for i,text in enumerate(texts):
                key=hashlib.sha256((json.dumps(self.identity,sort_keys=True)+text).encode()).hexdigest()
                path=self.cache/(key+'.json')
                if path.exists():result[i]=json.loads(path.read_text())
                else:missing.append((i,text,path))
            if missing:
                import numpy as np
                model=_sentence_model(self.settings.embedding_model)
                windows=[];groups=[]
                for _,text,_ in missing:
                    parts=_token_windows(model,text);start=len(windows)
                    windows.extend(value for value,weight in parts)
                    groups.append((start,len(windows),[weight for value,weight in parts]))
                vectors=model.encode(windows,
                    batch_size=32,normalize_embeddings=True,show_progress_bar=False,convert_to_numpy=True)
                if len(vectors)!=len(windows):raise ValueError('Invalid CPU embedding response')
                for (i,_,path),(start,end,weights) in zip(missing,groups):
                    vector=np.average(vectors[start:end],axis=0,weights=weights)
                    norm=np.linalg.norm(vector)
                    if not np.isfinite(vector).all() or not norm:raise ValueError('Invalid CPU embedding vector')
                    result[i]=(vector/norm).tolist();path.write_text(json.dumps(result[i]))
            if result and (not all(result) or len({len(v) for v in result})!=1):
                raise ValueError('Invalid or inconsistent CPU embedding dimensions')
            return result

    def embed_query(self,text):
        return self.embed_documents([text])[0]


def create_embedder(settings):
    if settings.embedding_provider=='ollama':return OllamaEmbedder(settings)
    if settings.embedding_provider=='sentence_transformers':return SentenceTransformerEmbedder(settings)
    raise ValueError('Unknown embedding provider: '+settings.embedding_provider)
