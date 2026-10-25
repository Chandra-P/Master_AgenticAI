"""Idempotent startup preparation for hosted visitors, serialized per process."""
from threading import RLock
import os

_INDEX_LOCK=RLock()


def apply_server_secrets(secrets):
    """Copy only known administrator settings; never expose them to widgets or logs."""
    for key in ('CIH_EMBEDDING_PROVIDER','CIH_GENERATION_PROVIDER','CIH_EMBEDDING_MODEL',
        'CIH_GENERATION_MODEL','CIH_AUTO_INDEX','CIH_OLLAMA_URL','GROQ_API_KEY',
        'OPENAI_API_KEY','CIH_CLASSIFICATION_PROVIDER','CIH_CLASSIFICATION_MODEL'):
        if key in secrets:
            os.environ[key]=str(secrets[key])


def prepare_indexes(service):
    with _INDEX_LOCK:
        from campaign_hub.chunking.pipeline import STRATEGIES
        for strategy in STRATEGIES:
            try:
                service.store(strategy)
            except ValueError as error:
                if not str(error).startswith(('Index missing','Index incompatible')):
                    raise
                service.index(strategy)
