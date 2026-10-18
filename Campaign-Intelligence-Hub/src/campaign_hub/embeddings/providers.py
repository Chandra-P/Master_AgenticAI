"""Ollama embeddings with bounded batches and content-addressed local cache."""
import hashlib
import json
import httpx


class OllamaEmbedder:
    def __init__(self, settings):
        self.settings = settings
        self.identity = {'provider':'ollama', 'model':settings.embedding_model, 'normalization':'embeddinggemma-query-document-v1'}
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
                response = httpx.post(self.settings.ollama_url+'/api/embed', json={'model':self.settings.embedding_model,
                    'input':[x[1] for x in batch], 'truncate':False}, timeout=180)
                response.raise_for_status()
                vectors = response.json()['embeddings']
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
