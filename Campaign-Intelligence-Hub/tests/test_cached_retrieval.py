def test_hybrid_retrieval_accepts_chunks_from_cached_module_generation():
    """Streamlit can retain a store while importing a new generation of models."""
    import importlib.util
    import campaign_hub.models as models
    from campaign_hub.retrieval.pipeline import retrieve
    spec=importlib.util.spec_from_file_location('previous_campaign_models',models.__file__)
    previous=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    chunk=previous.Chunk(chunk_id='source-1',text='Campaign acquisition goals',metadata={})
    assert not isinstance(chunk,models.Chunk)
    class CachedStore:
        def search(self,*args):return []
        def chunks(self,*args):return [chunk]
    hits=retrieve(CachedStore(),'campaign',{},models.RetrievalOptions())
    assert len(hits)==1
    assert hits[0].chunk.model_dump()==chunk.model_dump()
