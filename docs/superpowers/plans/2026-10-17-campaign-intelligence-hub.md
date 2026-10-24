# Campaign Intelligence Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Generate a complete, cited, eleven-section Campaign Performance Report from synthetic campaign documents, with a working retrieval explorer and evaluation dashboard.

**Architecture:** A project-local Python package owns deterministic corpus generation, Chroma-backed retrieval, evidence validation, and LangGraph report orchestration. Ollama provides local embeddings and generation. Streamlit calls these services; the CLI provides reproducible indexing and experiments.

**Tech Stack:** Python 3.12, Pydantic, Ollama, ChromaDB, LangGraph, Streamlit, tiktoken, rank-bm25, sentence-transformers, pytest.

**Spec:** `docs/superpowers/specs/2026-10-17-campaign-intelligence-hub-design.md`

## Global Constraints

- Project root: `Campaign-Intelligence-Hub/`; package: `src/campaign_hub/`. No nested Git repository.
- Default generation model: `llama3.2:3b`; embedding model: `embeddinggemma`; local Ollama API only by default. No automatic paid/cloud calls.
- Exactly 110 synthetic Markdown source documents and 30 gold evaluation items.
- Fixed chunking: 500 tokens with 50-token overlap; semantic chunking: business-heading sections with token-bounded splitting.
- Retrieve up to 20 candidates; select up to five unique chunks per evidence query. Reports require multiple section-specific queries.
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`. Never silently substitute another ranking method.
- Chroma collections and caches isolate corpus, chunker, tokenizer, provider/model, and embedding dimensions.
- Every finding requires inline source citations; generated reports are never automatically ingested as source evidence.
- Fallback: `I could not find sufficient evidence in the knowledge base.`
- All eleven report headings remain present; missing evidence produces explicit gaps and `partial` status.
- Four UI pages: Generate Report, Ask Questions, Retrieval Explorer, Evaluation Dashboard.
- No fabricated evaluation results or claims of guaranteed zero hallucinations.

## Review Focus

1. A stale index after changing model/corpus must fail with rebuild guidance, not return incompatible results (Task 4).
2. A similar historical campaign must never supply actual results for the selected campaign (Tasks 5 and 7).
3. Zero targets, lower-is-better KPIs, and mismatched reporting periods must not produce misleading comparisons (Task 6).
4. Missing source categories and model-produced invented citation IDs must yield gaps/fallbacks rather than a complete report (Tasks 6 and 7).
5. Widget reruns and an empty experiment directory must not launch repeated expensive jobs or show fabricated charts (Task 9).

## Execution conventions

Paths below are relative to `Campaign-Intelligence-Hub/` unless prefixed by `../`. Tests use temporary directories and deterministic model doubles unless explicitly marked `live`. Commands run in the project environment from its root: `.venv/Scripts/python.exe -m pytest ...` on Windows; `.venv/bin/python -m pytest ...` on Unix.

Each task owns its failing tests, minimal implementation, passing verification, and focused commit. Do not claim a task passes until its commands succeed. Preserve existing projects and untracked user files. Determine exact compatible dependency versions during environment setup, record them, and use installed Streamlit reference discovery before writing UI code.

### Task 1: Reproducible corpus and shared contracts

**Files:** Create `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`, `src/campaign_hub/__init__.py`, `config.py`, `models.py`, `synthetic_data/generator.py`, `synthetic_data/validation.py`, `tests/test_corpus.py`.

**Interfaces:** `Settings` owns project paths/provider/model settings; `CampaignRecord`, `SourceDocument`, `Chunk`, `SearchHit`, `EvidenceClaim`, `ReportSection`, `ReportResult`, and `EvaluationCase` are Pydantic contracts. `generate_corpus(output: Path, seed: int = 42) -> CorpusManifest`; `validate_corpus(root: Path) -> list[str]`. A report contains ordered sections, evidence ledger, status, confidence diagnostics, configuration, and provenance. Claims contain text and supporting chunk IDs. Source documents include all manifest metadata; search hits retain distinct dense/BM25/fusion/reranker fields.

- [ ] Write `test_corpus_counts_and_links`: assert counts `{brief:20, success_plan:20, performance_report:20, historical_deck:20, strategy:10, best_practice:10, kpi_dictionary:5, methodology:5}`, 20 unique campaigns, `TX-CHK-001`, consistent linked facts, synthetic notices, and identical bytes for the same seed.
- [ ] Run `pytest tests/test_corpus.py -q`; confirm failure because generator/contracts do not exist.
- [ ] Create the isolated environment and package configuration. Implement canonical fictional campaign records across all eleven campaign types, seeded rendering, budget/result arithmetic, metadata/manifest hashes, and 30 evaluation cases including complete, partial, and unsupported report requests. Produce atomic fact and section ground truth from records.
- [ ] Generate committed `data/corpus/`, `data/manifest.json`, and `data/evaluation/questions.json`. Run the corpus tests; require all counts/relationships and numeric checks to pass.
- [ ] Commit only Task 1 source, gold data, configuration, and tests; exclude virtual environments, indexes, credentials, caches, and generated report/run outputs.

### Task 2: Validated ingestion and two chunkers

**Files:** Create `ingestion/markdown.py`, `chunking/fixed.py`, `chunking/semantic.py`, `chunking/tokenizer.py`, `tests/test_chunking.py`, `tests/test_ingestion.py` under the package/test roots.

**Interfaces:** `load_documents(root: Path, manifest: CorpusManifest) -> list[SourceDocument]`; `chunk_documents(documents: list[SourceDocument], strategy: Literal['fixed','semantic']) -> list[Chunk]`. Each chunk retains all required metadata, stable source/section anchors, text hash, and tokenizer version.

- [ ] Write failing tests: `test_fixed_windows_are_500_with_50_overlap`, `test_semantic_sections_keep_campaign_and_heading`, `test_large_section_is_bounded`, `test_table_context_and_multisection_citations`, and `test_manifest_rejects_outside_paths_and_changed_hashes`.
- [ ] Run `pytest tests/test_chunking.py tests/test_ingestion.py -q`; confirm the missing implementation failures.
- [ ] Implement front-matter/heading parsing, manifest-owned path enforcement, actual tokenizer windows, section-aware attribution for cross-heading chunks, and bounded business-section splitting. Use tiktoken `cl100k_base` as the documented course tokenizer; separately enforce the embedding provider context budget and reject oversized inputs rather than silently truncate.
- [ ] Run the same tests against fixtures and all 110 source files; require stable chunk IDs and valid metadata with no source loss.
- [ ] Commit the ingestion/chunking implementation and tests.

### Task 3: Configurable local embedding and generation clients

**Files:** Create `embeddings/providers.py`, `generation/providers.py`, `tests/test_providers.py`, and model setup documentation in `README.md`.

**Interfaces:** `Embedder.embed_documents(texts: list[str]) -> list[list[float]]`, `Embedder.embed_query(text: str) -> list[float]`, `Embedder.identity -> dict`; `Generator.generate_json(system: str, prompt: str, schema: type[BaseModel]) -> BaseModel`. `build_embedder(settings: Settings) -> Embedder`; `build_generator(settings: Settings) -> Generator`.

- [ ] Write failing tests: no cloud requests by default; query/document formatting is distinct where required; bounded batches preserve order; invalid dimensions fail; model unavailable/timeouts return actionable errors; explicit OpenAI adapter selection requires a key.
- [ ] Run `pytest tests/test_providers.py -q` and observe missing-provider failures.
- [ ] Implement Ollama HTTP adapters, timeouts, response schema validation, context-budget checks, hash-keyed embedding caching, and explicit optional OpenAI embedding adapter. Download `embeddinggemma` only through deliberate setup. Use the existing generation model and record actual model identifiers.
- [ ] Run provider tests. Run a separately marked live embedding/query-generation smoke check; record vector dimensions and readiness without printing secrets.
- [ ] Commit provider adapters, tests, and setup instructions.

### Task 4: Persistent Chroma indexing with compatibility checks

**Files:** Create `vectordb/chroma_store.py`, `tests/test_index.py`.

**Interfaces:** `build_index(chunks: list[Chunk], embedder: Embedder, root: Path, strategy: str) -> IndexManifest`; `open_index(settings: Settings, strategy: str) -> ChromaStore`; `ChromaStore.search(query: str, filters: dict, k: int = 20) -> list[SearchHit]`.

- [ ] Write failing tests for persistence/reopen, deterministic upserts, removed-document cleanup, empty corpus, embedding-dimension/model change, chunker/corpus hash change, and incompatible-index rebuild messages.
- [ ] Run `pytest tests/test_index.py -q`; confirm failures before implementation.
- [ ] Implement persistent cosine Chroma collections, manifest comparison, stable IDs, source metadata/text storage, and batch indexing progress. Keep both strategies separately addressable; never mix embeddings or silently reuse stale indexes.
- [ ] Run temporary-directory integration tests; then build both real corpus indexes and verify reopening and one campaign-filtered query.
- [ ] Commit index code/tests and human-readable build metadata, excluding generated Chroma files and embedding caches.

### Task 5: Dense/hybrid retrieval and genuine reranking

**Files:** Create `retrieval/query.py`, `retrieval/bm25.py`, `retrieval/pipeline.py`, `reranking/cross_encoder.py`, `tests/test_retrieval.py`, `tests/test_reranking.py`.

**Interfaces:** `understand_query(question: str, campaign_id: str | None, manifest: CorpusManifest) -> QueryPlan`; `retrieve(plan: QueryPlan, settings: Settings, options: RetrievalOptions) -> list[SearchHit]`; `rerank(query: str, hits: list[SearchHit], enabled: bool) -> list[SearchHit]`. `RetrievalOptions` defines strategy, chunker, reranking, candidate_k=20, final_k=5, and typed metadata filters.

- [ ] Write failing tests for campaign/type/region/year filter parity, ID detection/unknown IDs, explicit cross-campaign historical search, RRF deduplication with `1/(60+rank)`, deterministic ties, maximum candidate/final counts, and real reranker failure disclosure.
- [ ] Run `pytest tests/test_retrieval.py tests/test_reranking.py -q` and confirm failures.
- [ ] Implement independent BM25/dense ranking with identical prefilters and RRF fusion. Historical/guidance scopes must be explicit QueryPlan fields. Load the actual cross-encoder for enabled mode and retain original ranks for diagnostics.
- [ ] Run deterministic tests plus a real dense/hybrid/reranker smoke query against the corpus; inspect current-versus-historical source ownership.
- [ ] Commit retrieval/reranking code and tests.

### Task 6: KPI arithmetic, grounded sections, and citation enforcement

**Files:** Create `reporting/kpis.py`, `reporting/evidence.py`, `reporting/render.py`, `reporting/prompts.py`, `tests/test_kpis.py`, `tests/test_evidence.py`, `tests/test_reports.py`.

**Interfaces:** `compare_kpis(targets: list[KpiValue], actuals: list[KpiValue]) -> list[KpiComparison]`; `validate_claims(claims: list[EvidenceClaim], evidence: dict[str, Chunk]) -> ValidationResult`; `render_report(report: ReportResult) -> str`. Extend `models.py` with the explicitly named supporting types. Comparison records carry unit/window, directionality, absolute/relative variance, status, and both citations.

- [ ] Write failing tests: higher/lower-is-better, zero target, missing actual, conflicting periods/units, invented IDs, cited-but-unsupported numeric claims, missing input categories, historical results attributed to current campaigns, and eleven required ordered headings.
- [ ] Run `pytest tests/test_kpis.py tests/test_evidence.py tests/test_reports.py -q` and confirm failures.
- [ ] Implement Decimal-based comparisons from parsed source values, source allowlists, numeric/support checks, evidence-gap tracking, conservative fallback, and Markdown inline citation/bibliography rendering. Preserve every heading and mark incomplete evidence as `partial`. Recommendations distinguish suggestions from observed outcomes. Confidence is an explainable heuristic, not a probability.
- [ ] Run the tests with hand-computed KPI fixtures and malicious source/model-output fixtures. Assert no report with unresolved required gaps is labeled complete and no invented citation is rendered.
- [ ] Commit report validation/rendering code and tests.

### Task 7: Executable LangGraph report and question workflows

**Files:** Create `langgraph/state.py`, `langgraph/workflow.py`, `reporting/service.py`, `tests/test_workflow.py`.

**Interfaces:** `build_workflow(settings: Settings) -> CompiledStateGraph`; `generate_report(campaign_id: str, period: str, options: RetrievalOptions) -> ReportResult`; `answer_question(question: str, campaign_id: str | None, options: RetrievalOptions) -> AnswerResult`. States expose section plan, inputs, evidence ledger, KPI comparisons, citations, validation, coverage, timings, and errors. All generation uses Task 3 clients; all retrieval uses Task 5.

- [ ] Write failing graph tests: query understanding and strategy routing, per-section 20-to-5 retrieval, separate historical/guidance searches, citations preserved through executive/storyline synthesis, missing core inputs, exact fallback, five-slide structure, and no report-output ingestion.
- [ ] Run `pytest tests/test_workflow.py -q` and confirm missing-workflow failures.
- [ ] Implement graph nodes/conditional edges for evidence planning, retrieval, optional reranking, context validation, structured generation, deterministic KPI attachment, citation validation, and complete/partial assembly. Summaries/storylines consume only validated facts plus their original evidence, bounded to model context.
- [ ] Run graph tests with deterministic doubles. Run one full local campaign report, one missing-evidence case, one focused answer, and one unsupported query; save actual diagnostics outside the source corpus.
- [ ] Commit workflows, report service, and tests.

### Task 8: Reproducible evaluation and CLI experiments

**Files:** Create `evaluation/metrics.py`, `evaluation/runner.py`, `evaluation/judge.py`, `cli.py`, `__main__.py`, `tests/test_metrics.py`, `tests/test_evaluation.py`.

**Interfaces:** `score_case(case: EvaluationCase, result: QueryResult) -> MetricResult`; `run_experiments(cases: list[EvaluationCase], settings: Settings, output: Path, smoke: bool = False) -> ExperimentManifest`. CLI commands: `generate`, `validate`, `index --chunking fixed|semantic|all`, `ask`, `report`, and `evaluate --smoke|--full`.

- [ ] Write failing tests with hand-computed MRR@5, nDCG@5, deduplicated precision/recall, valid citation matching/support, atomic-fact completeness, abstention accuracy, section coverage, stage timings, unavailable-judge scores as null, and resume invalidation on changed config/corpus.
- [ ] Run `pytest tests/test_metrics.py tests/test_evaluation.py -q` and confirm failures.
- [ ] Implement eight configurations, calibration/held-out separation, optional local entailment judge with provenance, raw answer/evidence persistence, aggregate CSV/JSON, progress, warm/cold timings, and resume keyed by immutable configuration. Never conflate proxy scores with faithfulness judgments.
- [ ] Run metric tests and smoke matrix, inspect actual outputs, then run full held-out experiments. Record actual completion or a precise external blocker; do not fabricate missing measurements.
- [ ] Commit evaluation/CLI code, tests, and course-safe measured experiment summaries; omit bulky caches and private credentials.

### Task 9: Four-page Streamlit application

**Files:** Create `app.py`, `.streamlit/config.toml`, `ui/resources.py`, `ui/report_page.py`, `ui/questions_page.py`, `ui/explorer_page.py`, `ui/evaluation_page.py`, `tests/test_ui.py`.

**Interfaces:** `get_services(settings: Settings)` caches resource objects using explicit configuration identity. UI pages call Tasks 7/8 contracts, not backend internals. All source views resolve through manifest-owned IDs.

- [ ] Run the developing-with-streamlit discovery script against the new environment and read its version-matched routing/reference files. Then write failing AppTest cases for four navigation pages, empty index, missing model, missing experiment directory, deliberate generation buttons, widget reruns without duplicate model calls, source expansion, and report download visibility.
- [ ] Run `pytest tests/test_ui.py -q`; confirm missing-page failures.
- [ ] Implement professional native Streamlit layout with visible synthetic-data labeling. Report is the landing page; show all eleven sections, KPI table, completeness/gaps, inline citations, source evidence, confidence explanation, and Markdown download. Provide shared retrieval controls, configuration comparisons, real metrics/charts, and actionable readiness messages. Index/evaluate only after explicit user actions.
- [ ] Run AppTest and launch the actual app. Visually inspect all four pages at desktop and narrow widths, one real report, source inspection, and nonempty measured evaluation charts. Resolve observed errors before completion.
- [ ] Commit UI code/configuration/tests.

### Task 10: Course documentation, root catalog, and final verification

**Files:** Finish `README.md`; create `docs/architecture.md`, `docs/methodology.md`, `docs/evaluation-results.md`, `docs/course-project.md`; modify `../README.md` to add Campaign Intelligence Hub without removing other projects.

**Interfaces:** Document the implemented CLI, actual artifact paths, actual supported providers, report schema, Mermaid workflow, metric definitions, confidence limits, and source provenance using implemented names/commands.

- [ ] Document Windows/Unix environment creation, dependencies, Ollama model pulls, corpus regeneration, indexing, Streamlit startup, CLI report generation, tests, and experiments. Clearly distinguish source performance/KPI reports from generated outputs and source citations from inferred suggestions.
- [ ] Run all non-live tests, then the tagged live smoke suite and documented CLI commands. Verify 110 corpus documents, 30 evaluation records, both real indexes, actual reranking, all eleven report sections, and recorded experiment provenance. Check Markdown relative links and `git diff --check`.
- [ ] Review the final diff for secrets, unintended files, unsupported completeness claims, untested arithmetic, and UI claims of fabricated metrics. Record remaining measured limitations rather than promise zero hallucinations.
- [ ] Commit the documentation and root catalog changes. Publish only within the user's authorized Git workflow and clearly identify the branch containing the app.

## Self-review

The plan covers the full spec: corpus (1), ingestion/chunking (2), free/local and optional providers (3), real Chroma (4), retrieval/reranking (5), grounding and arithmetic (6), actual LangGraph/report generation (7), experiments/CLI (8), UI (9), and course delivery (10). The five Review Focus conditions have named owning tests. All services use shared contracts; generated outputs stay outside corpus ingestion. Full implementation has not begun; execution follows user review of this plan and selection of execution method.
