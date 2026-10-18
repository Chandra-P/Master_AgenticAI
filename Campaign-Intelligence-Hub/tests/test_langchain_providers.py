def test_embedding_adapter_implements_langchain_contract(tmp_path):
    from langchain_core.embeddings import Embeddings
    from langchain_ollama import OllamaEmbeddings
    from campaign_hub.embeddings.providers import OllamaEmbedder
    from campaign_hub.config import Settings
    adapter=OllamaEmbedder(Settings(root=tmp_path))
    assert isinstance(adapter,Embeddings)
    assert isinstance(adapter.client,OllamaEmbeddings)


def test_generation_adapter_uses_structured_langchain_output():
    from langchain_ollama import ChatOllama
    from campaign_hub.generation.providers import OllamaGenerator
    from campaign_hub.config import Settings
    provider=OllamaGenerator(Settings())
    assert isinstance(provider.model,ChatOllama)
