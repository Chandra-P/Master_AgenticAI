"""Active RAG service: sources, indexes, retrieval and cited question answers only."""
import hashlib,json
from campaign_hub.config import Settings
from campaign_hub.models import FALLBACK
from campaign_hub.retrieval.filters import available_values,normalize_filters,merge_filters,FilterConflict
from campaign_hub.rag.grounding import question_plan


class RAGService:
    def __init__(self,settings=None):
        self.settings=settings or Settings()
        self.manifest=json.loads((self.settings.data/'manifest.json').read_text(encoding='utf-8'))
        self.campaigns={c['campaign_id']:c for c in self.manifest['campaigns']}
        self.corpus_hash=hashlib.sha256(json.dumps(self.manifest,sort_keys=True).encode()).hexdigest()
        self._stores={}

    @property
    def index_root(self):
        # Preserve earlier corpus collections instead of mutating historical indexes.
        return self.settings.data/'indexes'/('rag-'+self.corpus_hash[:12])

    def ensure_current(self):
        manifest=json.loads((self.settings.data/'manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()!=self.corpus_hash:
            raise ValueError('Corpus manifest changed; refresh and rebuild the indexes')
        from campaign_hub.synthetic_data.validation import validate_corpus
        if validate_corpus(self.settings.data):raise ValueError('Source documents changed; rebuild the corpus manifest and indexes')

    def store(self,strategy):
        self.ensure_current()
        if strategy not in self._stores:
            from campaign_hub.embeddings.providers import create_embedder
            from campaign_hub.vectordb.chroma_store import ChromaStore
            store=ChromaStore(self.index_root,strategy,create_embedder(self.settings))
            store.assert_compatible(self.corpus_hash)
            self._stores[strategy]=store
        return self._stores[strategy]

    def index(self,strategy):
        self.ensure_current()
        from campaign_hub.ingestion.markdown import load_documents
        from campaign_hub.chunking.pipeline import chunk_documents
        from campaign_hub.embeddings.providers import create_embedder
        from campaign_hub.vectordb.chroma_store import ChromaStore
        embedder=create_embedder(self.settings)
        chunks=chunk_documents(load_documents(self.settings.data,self.manifest),strategy,embedder=embedder)
        store=ChromaStore(self.index_root,strategy,embedder)
        store.build(chunks,self.corpus_hash)
        self._stores[strategy]=store
        return len(chunks)

    def search(self,query,campaign_id,options,document_type=None,filters=None):
        from campaign_hub.retrieval.pipeline import retrieve
        catalog=available_values(self.manifest)
        extra=normalize_filters(filters or {},catalog)
        if campaign_id and campaign_id not in catalog['campaign_id']:return []
        scope={}
        if campaign_id:scope['campaign_id']=[campaign_id]
        if document_type:scope['document_type']=[document_type]
        effective=merge_filters(extra,normalize_filters(scope,catalog))
        return retrieve(self.store(options.chunking),query,effective,options)

    def analyze_query(self,question,options,filters=None,campaign_id=None,automatic=True,
                      classification_provider=None,classification_model=None,answer_mode=False):
        from campaign_hub.retrieval.classification import classify_filters
        from campaign_hub.retrieval.pipeline import retrieve
        if not isinstance(question,str) or not 1<=len(question.strip())<=4000:
            raise ValueError('Enter a question of 1–4000 characters')
        catalog=available_values(self.manifest)
        manual=normalize_filters(filters or {},catalog)
        scope=normalize_filters({'campaign_id':campaign_id},catalog) if campaign_id else {}
        provider=(classification_provider or self.settings.classification_provider) if automatic else None
        model=(classification_model or (self.settings.classification_model if provider==self.settings.classification_provider
            else 'gpt-4.1-mini' if provider=='openai' else 'llama3.2:3b')) if automatic else None
        inferred=normalize_filters(classify_filters(question,catalog,self.settings,provider,model),catalog) if automatic else {}
        result={'manual_filters':manual,'scope_filters':scope,'inferred_filters':inferred,
                'classification_provider':provider,'classification_model':model,'hits':[]}
        try:effective=merge_filters(manual,scope,inferred)
        except FilterConflict as error:
            return {**result,'effective_filters':None,'status':'filter_conflict','message':str(error)}
        routing={};search_question=question
        if answer_mode and campaign_id and campaign_id!='GLOBAL':
            kind,expansion=question_plan(question,options)
            if kind and 'document_type' not in effective:
                routing=normalize_filters({'document_type':kind},catalog)
                effective=merge_filters(effective,routing);search_question+=expansion
        hits=retrieve(self.store(options.chunking),search_question,effective,options)
        if answer_mode and options.focus_context:
            from campaign_hub.retrieval.focus import focus_context
            hits=focus_context(question,hits)
        return {**result,'routing_filters':routing,'effective_filters':effective,
                'status':'retrieved' if hits else 'no_results','hits':[h.model_dump() for h in hits]}

    def answer_question(self,question,campaign_id,options,filters=None,automatic=False,
                        classification_provider=None,classification_model=None):
        if campaign_id and campaign_id not in self.campaigns and campaign_id!='GLOBAL':
            return {'answer':FALLBACK,'hits':[],'faithfulness':None,'status':'no_results'}
        from campaign_hub.rag.workflow import answer_workflow
        return answer_workflow(self,question,campaign_id,options,filters,automatic,
                               classification_provider,classification_model)
