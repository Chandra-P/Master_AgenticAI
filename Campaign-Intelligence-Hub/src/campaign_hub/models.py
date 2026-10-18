from pydantic import BaseModel, Field

FALLBACK = "I could not find sufficient evidence in the knowledge base."
SECTIONS = ["Executive Summary", "Goal Achievement Analysis", "KPI Performance Review",
            "Performance Drivers", "Audience Insights", "Channel Insights", "Recommendations",
            "Lessons Learned", "Suggested Next Steps", "Presentation Storyline", "Source Citations"]


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
    chunking: str = "semantic"
    retrieval: str = "hybrid"
    reranking: bool = False
    candidate_k: int = 20
    final_k: int = 5


class EvidenceClaim(BaseModel):
    text: str
    citations: list[str] = Field(default_factory=list)


class ReportSection(BaseModel):
    title: str
    claims: list[EvidenceClaim] = Field(default_factory=list)
    gap: str = ""


class ReportResult(BaseModel):
    campaign_id: str
    client_name: str = ''
    campaign_name: str = ''
    period: str
    sections: list[ReportSection]
    evidence: dict[str, Chunk]
    status: str
    confidence: float
    provenance: dict = Field(default_factory=dict)
    timings: dict = Field(default_factory=dict)
