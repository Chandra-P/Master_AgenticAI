# Campaign Intelligence Hub: system design

Date: 2026-10-17

Status: Proposed for user review; implementation has not started.

## Purpose and decisions

Build a Week 2 course application for campaign insights analysts. Transform campaign briefs, success plans, reports, historical insight decks, and methodology documents into evidence-backed answers and executive narratives.

Tagline: Transform campaign objectives, success plans, and performance reports into actionable insights and executive-ready narratives.

The user requires free API calls and previously had no API key. The default deployment therefore uses the existing local Ollama HTTP API: `llama3.2:3b` for generation and `embeddinggemma` for embeddings. No paid or cloud service is called automatically. Local inference uses the user's hardware; model downloads require internet access. OpenAI `text-embedding-3-small` remains an explicit optional adapter to honor the original embedding requirement, but is never selected or invoked without configuration and a key.

Alternatives considered: hosted free tiers introduce account/key requirements and changing quotas; local sentence-transformer embeddings remove the embedding service dependency but add a separate inference runtime. Ollama is preferred because it is already installed. Provider interfaces permit later substitution without changing retrieval logic.

## Scope and project boundaries

Create `Campaign-Intelligence-Hub/` inside the existing `Master_AgenticAI` repository. Maintain its own README, requirements, configuration example, tests, and course documentation; add a project entry to the root README. Do not create a nested Git repository or modify the other applications.

Use a Python package named `campaign_hub` under `src/`. Its subpackages mirror the requested architecture: `synthetic_data`, `ingestion`, `chunking`, `embeddings`, `vectordb`, `retrieval`, `reranking`, `evaluation`, `langgraph`, and `ui`. A namespaced `campaign_hub.langgraph` avoids shadowing the external `langgraph` package.

Additional top-level folders: `data/`, `docs/`, and `tests/`. Configuration and path resolution must work regardless of the shell's working directory. Ignore virtual environments, caches, local Chroma files, model caches, credentials, and generated run artifacts. Commit the synthetic Markdown corpus and ground truth so a clone is reproducible.

## Corpus and ground truth

Generate exactly 110 Markdown documents using seeded, deterministic Python generation:

| Type | Count |
| --- | ---: |
| Campaign briefs | 20 |
| Success plans | 20 |
| Performance reports | 20 |
| Historical insight decks | 20 |
| Strategy documents | 10 |
| Best practice guides | 10 |
| KPI dictionaries | 5 |
| Reporting methodologies | 5 |

Twenty fictional campaigns span the eleven requested banking/credit-union campaign types, multiple regions and years. Include `TX-CHK-001`. Each campaign's four primary documents share stable campaign/client metadata and consistent numerical facts. Clearly label all institutions, results, and recommendations as synthetic. No document-generation API calls are needed.

A canonical campaign record contains ID, name, client, type, region, year, objective, audience, offer, creative theme, channels, success metrics, KPI definitions, targets, budget, results, insights, lessons, and recommendations. Documents distribute those facts by purpose: briefs and plans contain prospective goals; reports and historical decks contain outcomes. Never imply that a brief knew future results.

Calculate derived metrics from canonical raw values, with explicit denominators, units, attribution windows, and rounding. Include both successful and underperforming campaigns and contradictory-looking cases resolved by methodology (e.g. clicks vs funded accounts). Manifest records document IDs, paths, campaign links, hashes, and schema version.

Generate 30 evaluation records with stable IDs, questions, expected answers, atomic expected facts, expected document IDs, and ground-truth section citations. Cover objectives, KPIs, results, cross-document comparisons, analogous campaigns, recommendations, executive summaries, slide storylines, and unsupported questions. Reserve a subset for threshold tuning; report final comparisons on the remaining questions. Ground truth comes from canonical records, not model-generated answers.

## Ingestion and chunking

Validate Markdown front matter, required metadata, linked campaign IDs, and file hashes. Parse headings into sections; assign stable source IDs and anchors.

Fixed chunking: tokenizer-based windows of 500 tokens with 50-token overlap, not word counts. Record tokenizer/version. Preserve section attribution even when a window crosses boundaries.

Semantic chunking: heading-based business sections (objectives, audience, offers, channels, KPI definitions, targets, criteria, findings, recommendations, lessons). Label this accurately as business-section chunking rather than learned semantic-breakpoint detection. Keep headings and tables intact where possible; split sections over the embedding context budget using token windows with overlap.

Every chunk carries campaign_id, campaign_name, client_name, campaign_type, region, year, document_type, section_name, document_id, source_path, section_anchor, chunk_id, token_count, and content_hash. Global guides use explicit corpus-wide metadata rather than masquerading as campaign-specific facts.

## Embeddings and Chroma

Separate configurable embedding and generation providers. Ollama clients have timeouts and actionable readiness/model-not-found errors. Embed in bounded batches and cache by provider, model, text hash, and normalization version. Apply provider-specific query/document formatting when required by the embedding model.

Use persistent Chroma cosine collections, separate for fixed and semantic chunks. Collection identity includes corpus hash, embedding provider/model/dimensions, tokenizer, and chunker configuration. Reject incompatible indexes and require rebuilding; never mix embeddings from different models. Reindex via deterministic IDs/upserts, with explicit invalidation for removed documents. Expose build progress in UI/CLI.

## Retrieval and reranking

Dense search retrieves up to 20 candidates. Hybrid search combines dense and BM25 candidates with reciprocal rank fusion, deduplicating by chunk ID. Apply identical campaign/type/region/year filters to both branches before fusion. Log component ranks and scores; do not present BM25, cosine, RRF, and reranker scores as interchangeable probabilities.

Campaign ID detection constrains factual questions to the selected campaign. Similarity/comparison questions deliberately permit other campaigns. Unknown IDs return insufficient evidence rather than silently searching a different campaign. UI filters override ambiguous inferred filters transparently.

Reranking uses the local `cross-encoder/ms-marco-MiniLM-L-6-v2` model, downloaded once, scoring query/chunk pairs. Reranking off preserves candidate order. Both modes send the top five unique chunks to context validation/generation. Download or inference failure produces an actionable error; never silently substitute lexical overlap while reporting cross-encoder reranking.

## LangGraph and evidence validation

```mermaid
flowchart TD
    Q[Question and user controls] --> U[Query understanding]
    U --> S[Strategy selection]
    S --> D[Dense retrieval]
    S --> H[Dense plus BM25 fusion]
    D --> R[Optional cross-encoder reranking]
    H --> R
    R --> V[Top five and context validation]
    V -->|Sufficient evidence| G[Grounded generation]
    V -->|Insufficient evidence| F[Evidence fallback]
    G --> C[Citation and claim validation]
    C -->|Supported| A[Final response]
    C -->|Invalid or unsupported| F
```

Graph state records query, intent, filters, selected strategy, candidates, contexts, answer fields, citations, validation findings, confidence diagnostics, timings, and errors. Nodes are independently testable and return explicit state updates.

Context validation considers semantic relevance, campaign match, coverage, and evidence availability. Thresholds are configurable and tuned only on the calibration subset. Confidence is a documented heuristic evidence score, not a calibrated probability of correctness.

Generation receives only retrieved evidence and instructions to treat source content as data, never commands. Return structured sections: executive summary, key findings, performance drivers, audience insights, recommendations, next steps, citations, and confidence. Recommendations must trace to source recommendations or clearly identified evidence-based synthesis; unsupported sections state insufficient evidence. Five-slide requests produce exactly five titled storyline entries with supporting citations.

Citations use allowlisted retrieved source IDs and section anchors. Validate cited IDs, actual source text, numerical claims, and required fact coverage. Reject invented or unsupported citations. An optional local LLM judge can assess claim entailment but is not a guarantee of truth. Conservative fallback is preferred when validation fails. A zero-hallucination guarantee is not technically supportable.

Fallback text is exactly: "I could not find sufficient evidence in the knowledge base." It has no fabricated citations and confidence zero; any partial retrieved sources may appear separately as diagnostic evidence, not support for an answer.

## Streamlit experience

Three navigation pages, consistent theme, clear synthetic-data labeling, and an evidence-focused layout. Use Streamlit's installed version-matched guidance before UI implementation.

Ask Questions: campaign/filter controls, example prompts, question input, fixed/semantic selector, dense/hybrid selector, reranking toggle, configurable local model, run status, required answer sections, source excerpts/links, confidence explanation, and download of the narrative as Markdown. PowerPoint storyline means narrative content; a binary PPTX export is outside the stated deliverables.

Retrieval Explorer: compare two configurations for the same question; show ranked chunks, actual source Markdown, metadata, retrieval/reranker scores with labels, and stage timings. Restrict source access to manifest-owned paths inside the corpus.

Evaluation Dashboard: load actual experiment JSON/CSV; filter configurations, compare retrieval/chunking/reranking results, inspect per-question answers and citations, and display charted metrics and latency. Display an honest empty state until evaluations run. Never populate charts with fabricated results.

Cache model/index resources across reruns with explicit configuration keys. Separate durable corpus/index files from per-session questions/results. Expensive ingestion and experiment runs require deliberate button/CLI execution, not automatic reruns on every widget change.

## Evaluation and experiments

Run the full 2 x 2 x 2 configuration matrix: fixed/semantic, dense/hybrid, reranking off/on. Use the same questions, corpus, embedding model, generation model, filters, and top-k to isolate configuration changes. Save seeds, dependency/model versions, corpus/index hashes, hardware description, and stage timings. Distinguish cold start from warm requests; no claims of statistical significance from a small course dataset.

Metrics: document relevance via MRR@5 and nDCG@5; context precision and recall against gold source documents/sections with duplicate handling; citation accuracy via valid cited source/section matches plus support checks; answer completeness via expected atomic facts; faithfulness via claim-level support judgments with judge provenance; and end-to-end/per-stage latency. Report unsupported-question abstention accuracy separately. Separate deterministic metric proxies from local LLM judge scores, and missing scores from zero scores. No judge access yields unavailable faithfulness rather than a fabricated perfect score.

CLI supports corpus generation/validation, indexing both chunkers, querying, smoke evaluation, and full experiments. Persist per-question raw outputs alongside aggregate CSV/JSON for auditability. CPU inference may make full evaluation lengthy; show progress and support resumption keyed to immutable experiment configuration.

## Verification and acceptance

Unit tests: exact corpus counts/relationships, numerical consistency, deterministic regeneration, metadata validation, fixed token window/overlap, semantic section attribution, cache/index invalidation, filter parity, fusion deduplication, reranker ordering, citation allowlists, unsupported-answer fallback, and evaluation math against hand-computed examples.

Integration tests: isolated temporary Chroma persistence, graph routing with deterministic test doubles, and offline synthetic-corpus end-to-end behavior. Live tests separately exercise Ollama embeddings/generation, real Chroma retrieval, cross-encoder reranking, one cited campaign answer, one unsupported question, and five-slide structure. Streamlit AppTest/smoke checks cover all pages, empty index/results states, and controls without triggering unintended expensive work.

Completion requires 110 committed source documents, 30 gold evaluation items, both real indexes, all retrieval modes, genuine reranking, actual LangGraph execution, source-validated responses/fallbacks, working UI, recorded experiment outputs or explicitly documented blocked runs, passing relevant checks, installation instructions, architecture diagram, and course methodology/limitations documentation. Do not call an unexecuted experiment a completed comparison.

## Delivery sequence

After this spec is approved, write a reviewable implementation plan. Implement corpus/contracts first, then ingestion/indexing, retrieval/reranking, graph/evidence checks, evaluations, UI, and final documentation. Use a project-specific virtual environment. Keep changes isolated from existing apps. Git publication follows the user's authorized repository workflow, with generated indexes, caches, and secrets excluded.
