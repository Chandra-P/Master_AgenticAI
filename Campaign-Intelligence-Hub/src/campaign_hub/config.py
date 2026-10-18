import os
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    ollama_url: str = os.getenv("CIH_OLLAMA_URL", "http://localhost:11434")
    generation_model: str = os.getenv("CIH_GENERATION_MODEL", "llama3.2:3b")
    embedding_model: str = os.getenv("CIH_EMBEDDING_MODEL", "embeddinggemma")

    @property
    def data(self):
        return self.root / "data"
