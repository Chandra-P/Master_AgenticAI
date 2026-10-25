import os
from pathlib import Path
from dataclasses import dataclass,field

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    ollama_url: str = field(default_factory=lambda:os.getenv('CIH_OLLAMA_URL','http://localhost:11434'))
    generation_provider: str = field(default_factory=lambda:os.getenv('CIH_GENERATION_PROVIDER','ollama'))
    embedding_provider: str = field(default_factory=lambda:os.getenv('CIH_EMBEDDING_PROVIDER','ollama'))
    generation_model: str = field(default_factory=lambda:os.getenv('CIH_GENERATION_MODEL',
        'qwen/qwen3.8-27b' if os.getenv('CIH_GENERATION_PROVIDER')=='groq' else
        'gpt-4.1-mini' if os.getenv('CIH_GENERATION_PROVIDER')=='openai' else 'llama3.2:3b'))
    classification_provider: str = field(default_factory=lambda:os.getenv('CIH_CLASSIFICATION_PROVIDER','ollama'))
    classification_model: str = field(default_factory=lambda:os.getenv('CIH_CLASSIFICATION_MODEL',
        'gpt-4.1-mini' if os.getenv('CIH_CLASSIFICATION_PROVIDER')=='openai' else 'llama3.2:3b'))
    embedding_model: str = field(default_factory=lambda:os.getenv('CIH_EMBEDDING_MODEL',
        'sentence-transformers/all-MiniLM-L6-v2' if os.getenv('CIH_EMBEDDING_PROVIDER')=='sentence_transformers' else 'embeddinggemma'))
    auto_index: bool = field(default_factory=lambda:os.getenv('CIH_AUTO_INDEX','false').lower() in ('true','1','yes'))

    @property
    def data(self):
        return self.root / "data"
