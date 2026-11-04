from pydantic import BaseModel, Field
from typing import Literal

FALLBACK = "I could not find sufficient evidence in the knowledge base."



class SourceDocument(BaseModel):
    metadata: dict
    text: str


class Chunk(BaseModel):
    chunk_id: str
    text: str
    metadata: dict


class SearchHit(BaseModel):
    chunk: Chunk
    score: float
    dense_score: float | None = None
    bm25_score: float | None = None
    rerank_score: float | None = None


class RetrievalOptions(BaseModel):
    chunking: Literal['fixed','section','semantic'] = "semantic"
    retrieval: str = "hybrid"
    reranking: bool = False
    candidate_k: int = 20
    final_k: int = 8
    focus_context: bool = False


class EvidenceClaim(BaseModel):
    text: str
    citations: list[str] = Field(default_factory=list)
