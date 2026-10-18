# Architecture

```mermaid
flowchart TD
    C[110 synthetic Markdown sources] --> I[Validated ingestion]
    I --> F[Fixed 500 tokens / 50 overlap]
    I --> S[Business-section chunking]
    F --> E[Local Ollama embeddings]
    S --> E
    E --> D[LangChain Chroma / persistent collections]
    U[Campaign report request] --> L[LangGraph coverage plan]
    L --> R[Per-section retrieval]
    D --> R
    B[BM25 source index] --> R
    R --> RR[Optional cross-encoder reranking]
    RR --> V[Campaign and period evidence checks]
    V --> G[Source-grounded sections and local generation]
    G --> K[Python KPI arithmetic and citation validation]
    K --> O[Eleven-section report with inline citations]
    V --> H[Compatible earlier channel cohorts]
    H --> P[Python peer median / rank / percentile]
    P --> O
    O --> UI[Streamlit preview / Markdown download]
```

Chroma stores chunk text, vectors, and source metadata. It does not generate answers. LangChain's OllamaEmbeddings converts source text/questions into embeddings; ChatPromptTemplate and ChatOllama structured-output chains provide generation. LangChain Chroma performs vector search. BM25 complements vector search for exact identifiers and terminology. Report sections use independent retrieval queries rather than sharing only five chunks for a whole report.

Direct mail uses 60 days from mail/drop date; display uses 30 days from exposure. Historical comparisons use retrieved channel outcome tables and require compatible product/channel/measurement rules, an earlier reporting period, and mature attribution windows. The UI and report show peer-level evidence, medians, ranks, and direction-aware performance percentiles.

Generated reports remain outside the ingestion manifest. This prevents output text becoming circular evidence. Source access is limited to manifest paths. Historical evidence is explicitly labeled and cannot supply the selected campaign's KPI actuals.
