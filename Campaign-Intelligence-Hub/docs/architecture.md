# Architecture

```mermaid
flowchart TD
    C[110 synthetic Markdown sources] --> I[Validated ingestion]
    I --> F[Fixed 500 tokens / 50 overlap]
    I --> S[Business-section chunking]
    F --> E[Local Ollama embeddings]
    S --> E
    E --> D[Persistent Chroma collections]
    U[Campaign report request] --> L[LangGraph coverage plan]
    L --> R[Per-section retrieval]
    D --> R
    B[BM25 source index] --> R
    R --> RR[Optional cross-encoder reranking]
    RR --> V[Campaign and period evidence checks]
    V --> G[Source-grounded sections and local generation]
    G --> K[Python KPI arithmetic and citation validation]
    K --> O[Eleven-section report with inline citations]
    O --> UI[Streamlit preview / Markdown download]
```

Chroma stores chunk text, vectors, and source metadata. It does not generate answers. Local Ollama converts source text/questions into embeddings and optionally generates structured prose. BM25 complements vector search for exact identifiers and terminology. Report sections use independent retrieval queries rather than sharing only five chunks for a whole report.

Generated reports remain outside the ingestion manifest. This prevents output text becoming circular evidence. Source access is limited to manifest paths. Historical evidence is explicitly labeled and cannot supply the selected campaign's KPI actuals.
