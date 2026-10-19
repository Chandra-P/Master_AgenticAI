# Implementation status report

Audit date: 2026-10-18. Scope: the user's 102-item implementation checklist and the client presentation workspace. Every checklist item below is either **IMPLEMENTED** or explicitly **FUTURE WORK**. Implemented describes existing executable code or delivered documentation; it does not imply a production rollout or perfect factual accuracy.

## Implemented features

The application includes the deterministic synthetic corpus, LangChain/Chroma RAG with local Ollama and hosted CPU/Groq profiles, three distinct chunkers, retrieval experiments, a configurable cross-encoder, a three-page client Streamlit workspace with retained technical development views, automatic campaign geography, same-client historical comparisons, and standalone HTML client presentations with embedded charts and insights. Final generation retrieves chunks, expands validated parent documents, and uses source text and deterministic arithmetic. Unsupported model prose cannot enter the final presentation packet. The map remains a fast source-table snapshot. HTML is the default client output; PDF/PowerPoint export functions are retained only for compatibility. See the [deliverable audit](deliverable-audit.md) for comparison with the supplied peer solution kits.

Report cover identity, all KPI units/directions/periods, plan targets, campaign/channel/geographic totals, source versions, citations and attribution maturity are checked. Every export revalidates the packet. Audience and channel observations are distinguished from causal lift; unmeasured ROI is unavailable. Small historical cohorts and synthetic data are disclosed. Balances mean opening account balances in USD, not revenue or current deposits.

## Missing features

The eight checklist gaps are explicitly FUTURE WORK: a calibrated confidence-score UI, six independently executable graph nodes (retrieval, hybrid search, reranking, context validation, generation and citation generation), and a measured embedding-model comparison. The current graph calls these pipeline functions through a combined report node; they are not misrepresented as separate graph nodes.

## Project readiness score

**92.2% checklist implementation coverage: 94 IMPLEMENTED / 102 items.** The eight future-work items receive zero credit. This is a feature-coverage score, not accuracy, security, quality assurance, or production readiness. The synthetic local demonstration is usable; production rollout remains future work pending the operational items below.

## Complete checklist

Paths below are relative to the project. Validation commands and measured results are in [evaluation results](evaluation-results.md). The final client layout combines the original analytical topics into the client's requested sections; the eleven-section analytical report remains available through the `report` CLI and LangGraph workflow.

### Data

| Item | Status | Evidence / boundary |
|---|---|---|
| Synthetic data generator | IMPLEMENTED | `synthetic_data/generator.py`; seeded and reproducible |
| 20 Campaign Briefs | IMPLEMENTED | `data/corpus/brief`; manifest count 20 |
| 20 Success Plans | IMPLEMENTED | `data/corpus/success_plan`; count 20 |
| 20 Campaign Performance Reports | IMPLEMENTED | `data/corpus/performance_report`; count 20 |
| 20 Historical Insight Decks | IMPLEMENTED | `data/corpus/historical_deck`; 20 Markdown deck-source documents; not 20 PPTX files |
| 10 Strategy Documents | IMPLEMENTED | `data/corpus/strategy`; count 10 |
| 10 Best Practice Guides | IMPLEMENTED | `data/corpus/best_practice`; count 10 |
| 5 KPI Dictionaries | IMPLEMENTED | `data/corpus/kpi_dictionary`; count 5 |
| 5 Reporting Methodology Documents | IMPLEMENTED | `data/corpus/methodology`; count 5 |
| Metadata generation | IMPLEMENTED | YAML front matter, manifest, content hashes, client/product/channel/period metadata |
| Cross-document relationships | IMPLEMENTED | Campaign ID joins brief, plan, results and deck; document IDs and source citations preserve links |

### RAG pipeline

| Item | Status | Evidence / boundary |
|---|---|---|
| Document ingestion | IMPLEMENTED | `ingestion/markdown.py`; hash/path validation |
| Document cleaning | IMPLEMENTED | Heading extraction and whitespace stripping remove front matter/title from chunk bodies; Markdown only |
| Metadata extraction | IMPLEMENTED | Validated source manifest metadata; YAML parsing in factual snapshot |
| Embedding pipeline | IMPLEMENTED | `embeddings/providers.py`; batching and content-addressed cache |
| ChromaDB vector database | IMPLEMENTED | `vectordb/chroma_store.py`; LangChain Chroma + PersistentClient |
| Metadata-aware retrieval | IMPLEMENTED | Campaign/document-type filters applied to dense and lexical candidates |
| Source attribution | IMPLEMENTED | Source/chunk IDs, section anchors, metadata, hashes and report bibliography |

### Chunking

| Item | Status | Evidence / boundary |
|---|---|---|
| Fixed chunking implementation | IMPLEMENTED | `chunking/pipeline.py`; 500 tokens, 50 overlap |
| Semantic chunking implementation | IMPLEMENTED | `chunking/semantic.py`; sentence/unit embeddings and 65th-percentile cosine breakpoints, source spans and bounded overflow. Heading-based splitting remains separate as `section` |
| Chunking comparison experiment | IMPLEMENTED | Twelve configurations across fixed/section/semantic, dense/hybrid and rerank off/on; historical eight-configuration results are labeled separately |
| Chunk metadata storage | IMPLEMENTED | Token count, strategy, tokenizer, source/section and content hash stored in Chroma |

### Retrieval

| Item | Status | Evidence / boundary |
|---|---|---|
| Dense retrieval | IMPLEMENTED | LangChain Chroma similarity search |
| Hybrid retrieval | IMPLEMENTED | Dense/BM25 reciprocal-rank fusion |
| BM25 retrieval | IMPLEMENTED | `retrieval/pipeline.py`; lexical leg of hybrid search, no standalone BM25 UI mode |
| Top-K retrieval | IMPLEMENTED | Candidate K and final K in `RetrievalOptions` |
| Retrieval comparison experiment | IMPLEMENTED | Dense/hybrid across three chunkers and reranking states |

### Reranking

| Item | Status | Evidence / boundary |
|---|---|---|
| Reranker implementation | IMPLEMENTED | `reranking/cross_encoder.py`; real cross-encoder model |
| Reranking toggle | IMPLEMENTED | UI checkbox and `--rerank` |
| Reranking evaluation | IMPLEMENTED | On/off experiment configurations |
| Reranking comparison metrics | IMPLEMENTED | Relevance, precision/recall and latency by configuration |

### LangChain / LangGraph

| Item | Status | Evidence / boundary |
|---|---|---|
| Query understanding node | IMPLEMENTED | `langgraph/workflow.py`; static report source plan, not general semantic intent parsing |
| Retrieval node | FUTURE WORK | Retrieval function executes inside combined report node; split into a separately testable graph node |
| Hybrid search node | FUTURE WORK | Hybrid function implemented; independent graph state/node pending |
| Reranker node | FUTURE WORK | Reranker implemented; independent conditional graph node pending |
| Context validation node | FUTURE WORK | Source/context checks exist in service; independent pre-generation graph node pending |
| Generation node | FUTURE WORK | Generation executes inside combined node; independent graph node pending |
| Citation generation node | FUTURE WORK | Citations generated by service and checked by graph citation-validation node; separate citation-generation node pending |
| End-to-end graph workflow | IMPLEMENTED | Query plan → combined retrieval/rerank/generation → citation validation; LangChain models/embeddings/vector store |

### ChromaDB

| Item | Status | Evidence / boundary |
|---|---|---|
| Persistent ChromaDB setup | IMPLEMENTED | `data/indexes`; PersistentClient |
| Collection creation | IMPLEMENTED | Strategy + embedding identity collection names |
| Metadata schema | IMPLEMENTED | Source/campaign/client/period/section/chunk metadata; semantic character spans, boundary reason, threshold and segmentation embedder |
| Document indexing | IMPLEMENTED | Upserts, stale chunk deletion, compatibility manifest |
| Query functionality | IMPLEMENTED | Filtered similarity search and lexical candidate enumeration |

### Open-source models

| Item | Status | Evidence / boundary |
|---|---|---|
| Llama generation model | IMPLEMENTED | LangChain ChatOllama; `llama3.2:3b` default |
| Open-source embedding model | IMPLEMENTED | Ollama `embeddinggemma` local default; CPU all-MiniLM-L6-v2 hosted profile |
| Configurable model selection | IMPLEMENTED | Environment variables, generation model UI; embedding changes require rebuild |

### Streamlit UI

| Item | Status | Evidence / boundary |
|---|---|---|
| Modern landing page | IMPLEMENTED | Navy sidebar, warm gray/teal theme, KPI cards, client/campaign selectors, automatic map |
| Ask Questions page | IMPLEMENTED | `ui/questions_page.py` |
| Response display | IMPLEMENTED | Grounded answer with abstention behavior |
| Citation display | IMPLEMENTED | Answer citation IDs and inspectable source evidence |
| Confidence scores | FUTURE WORK | No calibrated probability-of-truth score. Analytical reports expose evidence coverage; UI readiness is source validation, not confidence |
| Retrieval Explorer page | IMPLEMENTED | `ui/explorer_page.py`; retained for development, removed from client navigation at user request |
| Retrieved chunk viewer | IMPLEMENTED | Source text and rank/score display |
| Metadata viewer | IMPLEMENTED | Per-chunk metadata JSON |
| Evaluation Dashboard page | IMPLEMENTED | `ui/evaluation_page.py`; retained for development, removed from client navigation at user request; rejects stale-corpus results |
| Faithfulness metrics | IMPLEMENTED | Optional claim support judge and actual RAGAS assessment; null unless measured. Saved profiles and case coverage expose same-model/limited-sample boundaries |
| Retrieval metrics | IMPLEMENTED | MRR, nDCG, document precision/recall |
| Latency metrics | IMPLEMENTED | Actual elapsed seconds per run/configuration |
| Comparison visualizations | IMPLEMENTED | Charts grouped by chunking/retrieval/reranking |

### User controls

| Item | Status | Evidence / boundary |
|---|---|---|
| Fixed chunking toggle | IMPLEMENTED | Analyst chunking selector / CLI |
| Semantic chunking toggle | IMPLEMENTED | Separate Fixed-size, Section-based and Embedding-based semantic choices in controls, explorer and CLI |
| Dense retrieval toggle | IMPLEMENTED | Analyst retrieval selector / CLI |
| Hybrid retrieval toggle | IMPLEMENTED | Same selector |
| Reranking toggle | IMPLEMENTED | Cross-encoder checkbox / CLI |

### Campaign report generation

| Item | Status | Evidence / boundary |
|---|---|---|
| Executive Summary generation | IMPLEMENTED | Source-checked deterministic client summary; analytical report also available |
| Campaign Goal Analysis | IMPLEMENTED | Goals and Progress Toward Goals; target reconciliation |
| KPI Achievement Analysis | IMPLEMENTED | Activation, spend, acquisition cost and opening balance calculations |
| Performance Driver Analysis | IMPLEMENTED | Source-backed observed channel contribution; no causal claims |
| Audience Insights | IMPLEMENTED | Sourced existing/prospective totals; unmeasured demographics unavailable |
| Channel Insights | IMPLEMENTED | Direct mail/display outcomes, denominators, spend and attribution |
| Recommendations | IMPLEMENTED | Historical and best-practice source evidence; proposed tests labeled |
| Lessons Learned | IMPLEMENTED | Learnings section with citations |
| Next Steps | IMPLEMENTED | Source-backed actions; unsupported owner/date/priority left unassigned |
| PowerPoint Storyline generation | IMPLEMENTED | Analytical storyline and legacy editable export retained; user superseded primary presentation format with chart-led HTML |
| Citation-backed report generation | IMPLEMENTED | Standalone HTML with 10 default-campaign charts, adjacent findings, expandable source evidence and frozen JSON retrieval packet |

### Evaluation

| Item | Status | Evidence / boundary |
|---|---|---|
| 30 evaluation questions | IMPLEMENTED | `data/evaluation/questions.json`; 3 calibration + 27 held-out |
| Ground truth answers | IMPLEMENTED | Expected answers and facts; synthetic source-derived gold |
| Expected citations | IMPLEMENTED | Expected document IDs and source section anchors |
| Automated evaluation script | IMPLEMENTED | `evaluation/runner.py`; CLI `evaluate` |

### Metrics

| Item | Status | Evidence / boundary |
|---|---|---|
| Retrieval relevance | IMPLEMENTED | MRR@5 and nDCG@5 |
| Faithfulness | IMPLEMENTED | Optional explicit support judge and RAGAS claim-level metric; unmeasured/failed values remain null |
| Citation accuracy | IMPLEMENTED | Gold source/section overlap proxy, not semantic entailment |
| Completeness | IMPLEMENTED | Expected-fact matching and section coverage; not overall narrative-quality scoring |
| Context precision | IMPLEMENTED | Document fraction in retrieval experiments; separate actual RAGAS rank-sensitive passage precision in opt-in generated-answer assessments |
| Context recall | IMPLEMENTED | Expected document coverage in retrieval experiments; separate RAGAS reference-claim coverage in generated-answer assessments |
| Latency | IMPLEMENTED | Measured wall-clock seconds, including local cold-start effects |

### Experiments

| Item | Status | Evidence / boundary |
|---|---|---|
| Fixed chunking vs semantic chunking | IMPLEMENTED | Actual matrix outputs |
| Dense retrieval vs hybrid retrieval | IMPLEMENTED | Actual matrix outputs |
| No reranking vs reranking | IMPLEMENTED | Actual matrix outputs |
| Embedding model comparison | FUTURE WORK | Both embeddinggemma and MiniLM profiles have measurements, but no controlled matched-model experiment with identical chunker versions/cases and quality/latency/storage comparisons has been completed |

### Visualizations

| Item | Status | Evidence / boundary |
|---|---|---|
| Retrieval comparison charts | IMPLEMENTED | Evaluation dashboard grouped MRR/precision/recall |
| Chunking comparison charts | IMPLEMENTED | Three chunkers across twelve configuration labels; bundled CPU measurements are distinct from hosted performance |
| Reranking impact charts | IMPLEMENTED | On/off configurations visible in chart labels |
| Faithfulness charts | IMPLEMENTED | Conditional chart shown only when measured non-null judge results exist; current retrieval-only run has no such values |
| Latency charts | IMPLEMENTED | Measured seconds by configuration |

### Deployment

| Item | Status | Evidence / boundary |
|---|---|---|
| requirements.txt | IMPLEMENTED | Includes UI/RAG/report export dependencies |
| Environment variables | IMPLEMENTED | `.env.example` and `config.py`; shell-exported values |
| README | IMPLEMENTED | Main project setup, workflows, limits and artifact links |
| Setup instructions | IMPLEMENTED | Windows and cross-platform notes |
| Streamlit deployment instructions | IMPLEMENTED | [Deployment guide](deployment.md); local/managed server |
| Streamlit Community Cloud deployment guide | IMPLEMENTED | Live CPU/Groq deployment, visitor access and chart-led report checks documented in cloud-quickstart.md; model credentials remain server-side |

## Future enhancements and release boundaries

1. Complete the eight checklist gaps above, with graph-node tests and a reproducible second-embedding-model experiment. Calibrate any confidence score against independently labeled real cases before displaying it as confidence.
2. Real client data ingestion/connectors, row-level access controls, authentication, client isolation, audited analyst approval, report version storage and durable multi-user persistence. Current selectors filter synthetic campaign data; they are not an authorization system.
3. Verified, licensed industry benchmark data with industry/product/geography/window eligibility, publication date and sample sizes. Fictional cross-client references must never be labeled real industry performance.
4. Independent human factual evaluation, a complete independently judged generated-answer benchmark, model upgrade regression suites and an accepted real-data quality threshold. Optional RAGAS scoring and a small local smoke assessment do not establish broad narrative faithfulness or abstention quality. See [RAGAS assessment](ragas-assessment.md).
5. Full accessibility testing, cloud resource/load/restart tests and production model-hosting controls. A live Community Cloud demo, incognito visitor access, cited answers and a chart-led report preview have been verified. The HTML example was checked in Edge at desktop/mobile viewport sizes; these checks are not a comprehensive accessibility, capacity or production browser test matrix.
6. Broader source schemas, arbitrary spreadsheet/PDF/slide ingestion and zero-total campaign KPI support. The current typed synthetic Markdown contract blocks unsupported schemas rather than guessing. Zero-activation channel CPA is unavailable; campaign-wide zero-activation cost handling needs a separate source contract.
7. Client-specific HTML brand templates, richer interactive chart filtering and account-level geospatial integration. Current HTML embeds portable SVG comparison charts; map points are approximate synthetic city aggregates.

No claim of 100% factual correctness or production readiness is made. Presentation exports passing the implemented checks are ready for analyst review within the supported synthetic schema.
