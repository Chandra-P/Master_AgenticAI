# Campaign Intelligence Hub

Transform campaign objectives, success plans, and performance reports into actionable insights and executive-ready narratives.

A Week 2 RAG course project for campaign insights analysts. The main output is a Campaign Performance Report grounded in a fictional banking/credit-union corpus, with inline source citations, KPI comparisons, and an evidence-coverage checklist.

## What is included

### Review deliverables

- [Word project overview](docs/Campaign_Intelligence_Hub_Project_Overview.docx): three-page explanation with campaign examples, a simple fixed-versus-semantic explanation, the measured comparison and next steps. Detailed implementation remains in the separate HTML technical kit.
- [Technical Solution Kit](docs/technical_solution_kit.html): architecture, component deep dives, exact runtime prompts, decisions, measured comparisons, setup and explicit implementation boundaries.
- [Executive Campaign Performance Dashboard](docs/campaign_performance_dashboard.html): interactive Chart.js comparisons, KPI target/variance/status cards, audience composition, attribution timeline, adjacent findings/actions, recommendations, seven-part presentation storyline and source evidence.

Both files embed Bootstrap CSS and Chart.js locally and work without a CDN. SVG/data-table fallbacks preserve readable charts when JavaScript is blocked or the report is printed. Rebuild them from the validated saved example packet with `python -m campaign_hub.deliverables`. Generate that packet first with `python -m campaign_hub client-report --campaign TX-CHK-001` if it is absent.

The dashboard explicitly marks unsupported trends, funded-account stages, funnel events and financial ROI as unavailable. Opening balances are not net deposit growth. Findings are derived from cited source tables; causes and projected impacts are not invented. See the [new deliverable requirements audit](docs/visual-deliverable-status.md).

- 110 deterministic synthetic Markdown documents for 20 campaigns and shared guidance.
- 30 evaluation cases with expected facts and source/section citations.
- LangChain `OllamaEmbeddings`, `ChatOllama`, prompt/structured-output chains, and the LangChain Chroma integration; no API key or paid API calls by default.
- Persistent ChromaDB with fixed-size, section-based, and embedding-based semantic chunks. All use a 500-token bound and 50-token overflow overlap; semantic boundaries use sentence/unit embeddings and cosine-distance percentiles.
- Dense retrieval, dense/BM25 reciprocal-rank fusion, and optional real cross-encoder reranking.
- LangGraph report orchestration and explicit insufficient-evidence behavior.
- Streamlit report generation, historical campaign comparison, questions, retrieval exploration, and measured evaluation views.
- Automatic client/campaign map showing attributed accounts and opening balances, with channel filters and a geographic results table.
- A standalone HTML client presentation with embedded Chart.js comparisons, SVG/table fallbacks, findings directly below each chart, and clickable source evidence. The final report retrieves chunks through Chroma, expands validated source documents, and calculates metrics in Python.

See the complete [implementation status report](docs/implementation-status.md): **94 of 102 checklist items implemented (92.2%)**, with eight explicit future-work items and production release boundaries. See the [deployment guide](docs/deployment.md) for local/server/Community Cloud instructions.

See the [three-method chunking comparison](docs/chunking-comparison.md) and [deliverable audit](docs/deliverable-audit.md) for the distinction between structural and embedding-based boundaries, experiment rules, and remaining requirements. The earlier heading-based `semantic` mode is now `section`; `semantic` now means actual embedding-based topic segmentation. Rebuild all indexes after updating.

**[Open the live demo](https://campaign-intelligence.streamlit.app/)** with no installation or visitor API key. Public access, cited Groq answers, and hosted chart-led report generation were checked on 2026-10-18. The [cloud quickstart](docs/cloud-quickstart.md) documents the deployment and verification limits. Hosting uses Streamlit Community Cloud, server-side CPU embeddings, automatic Chroma indexes and Groq generation; free-tier sleeping and API quotas apply. Local Ollama remains the default for local setup.

## Channels, attribution, and historical standing

Only **direct mail** and **display** are included:

| Channel | Attribution window | Starting event | Activation-rate denominator |
| --- | --- | --- | --- |
| Direct mail | 60 days | Mail/drop date | Mailed households |
| Display | 30 days | Exposure date | Unique exposed users |

Windows include the anchor date through the channel's final elapsed-day boundary; earlier/later conversions are excluded. The synthetic records use date-level cohorts and deduplicated outcomes assigned to one eligible channel. A campaign is mature only when its complete channel window has elapsed.

Use **Historical Comparison** to see activation rate and cost per activation against earlier campaigns of the **same client**, product type, channel, attribution rule, and denominator. An optional cross-client view is labeled **Synthetic peer reference — not an industry benchmark**. The page shows individual peers, peer medians, rank (1 = best), and a performance percentile with tie handling. Lower acquisition cost is better. Rates are compared within channels, not pooled across direct mail and display.

The same source-cited comparison appears in the client report's Progress Toward Goals. This 20-campaign corpus spans eleven product types and five fictional clients; the default campaign has two same-client historical comparators. Some products have no history. Small samples are explicitly flagged; a rank is a descriptive comparison, not a claim that a campaign is universally good. No compatible mature history means no ranking. Verified industry benchmark data has not been supplied.

```powershell
python -m campaign_hub compare --campaign TX-CHK-001
```

## Setup (Windows PowerShell)

Use Python 3.12 or newer and install [Ollama](https://ollama.com/download).

```powershell
cd Campaign-Intelligence-Hub
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
ollama pull llama3.2:3b
ollama pull embeddinggemma
python -m campaign_hub generate
python -m campaign_hub validate
python -m campaign_hub index --chunking all
python -m streamlit run app.py
```

If activation is blocked, replace `python` with `.\.venv\Scripts\python.exe`. On macOS/Linux activate with `source .venv/bin/activate`. Commands can use absolute file paths; data paths resolve from the project, not the shell working directory. Keep Ollama running. Initial installation and model downloads require internet access; local generation/embedding do not require paid calls.

## Generate a report

Select **Generate Report**, choose a **Client**, then choose one of that client's campaigns. KPI cards, map and same-client historical standing update automatically. Use the channel and map-measure controls to inspect accounts or opening balances. Click **Generate client-facing report** to retrieve evidence and see the HTML presentation preview. Choose **Download HTML presentation**, then open the file in a browser. Client and campaign selectors also appear on Historical Comparison and Ask Questions. Analyst View adds metadata classification and evidence inspection; the older Retrieval Explorer and Evaluation Dashboard remain development modules outside app navigation.

The HTML presentation includes client/campaign identity, Executive Summary, Goals, chart-led Progress Toward Goals, Channels, Same-client History, Geography, Learnings, Recommendations, Next Steps, Measurement Notes and Source Citations. Each comparison chart has an adjacent insight and numbered source links. The file is self-contained and needs no CDN or network connection to view. Reconciliation failures, altered narrative, missing required retrieval evidence or immature attribution block exports. Proposed tests are labeled; owner/date/priority remain unassigned when absent from sources. These checks do not guarantee 100% correctness. The source corpus and client names are synthetic.

## Metadata classification and analyst view

Choose **Analyst View** to inspect retrieval without generating an answer. Enter a
question and optionally combine campaign ID, client, campaign type, region, year,
reporting period and document type. Values within one field use OR; different
fields use AND. The same effective filter scopes dense and BM25 retrieval.
Only values present in the corpus are accepted; a requested period not in the
corpus is rejected rather than silently replaced.

**Automatically classify metadata** defaults to local Ollama (`llama3.2:3b`).
Model choices are constrained to labels or supported aliases mentioned in the
question, and each inferred constraint must quote supporting words from it.
General questions without metadata terms use no inferred filters and need no
classification call. Use manual controls for unsupported paraphrases and shared
`ALL`/`GLOBAL` values. These guards check provenance, not full semantic entailment;
inspect the displayed filters before relying on the results.
The result shows manual selections, selected campaign scope, inferred filters,
question-routing filters, effective filters and ranked evidence. Expand evidence
to inspect source text, metadata and available ranking scores. Scores are not
confidence probabilities. Conflicting manual/inferred constraints stop the search;
empty results never trigger an unfiltered retry. Disable classification for
manual-only retrieval. Input edits hide stale results; only **Find evidence**
starts inference and retrieval.

**Ask Questions** uses the same controls while keeping its selected campaign
binding and retaining source-validated answers. Report calculations and historical
comparison eligibility are unchanged. The older comparison explorer and evaluation
dashboard remain development modules outside app navigation.

### Optional OpenAI alternative

Ollama remains the default for classification and local answer generation.
Select **openai** explicitly in **Classification provider** or the sidebar's
**Answer provider**. The default OpenAI model is `gpt-4.1-mini`; a configured
model must support structured outputs. Embeddings and Chroma indexes retain
their configured provider; choosing OpenAI answers does not re-embed the corpus.

Configure `OPENAI_API_KEY` in your process environment or the ignored
`Campaign-Intelligence-Hub/.streamlit/secrets.toml`, never in source files or a
widget. A placeholder-only example is in `.streamlit/secrets.example.toml`.
OpenAI classification sends your question and the allowed metadata values;
OpenAI answers also send retrieved passages. These calls use your API account.
There is no automatic fallback between local and hosted providers.

Optional server settings: `CIH_CLASSIFICATION_PROVIDER` (`ollama` by default)
and `CIH_CLASSIFICATION_MODEL` (`llama3.2:3b` by default, or `gpt-4.1-mini` for
an explicitly configured OpenAI classifier). `CIH_GENERATION_PROVIDER` and
`CIH_GENERATION_MODEL` independently control the answer provider.
The app reads process environment and private Streamlit secrets; it does not
automatically load a project `.env` file.

OpenAI request handling follows the official
[Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

Open the [example HTML presentation](docs/campaign_performance_dashboard.html). HTML is now the default client output in the UI and CLI; PDF/PowerPoint are no longer generated by that workflow. The obsolete PDF/PowerPoint exporters and their dependencies have been removed.

```powershell
python -m campaign_hub client-report --campaign TX-CHK-001
```

The final report uses the selected fixed-size/section-based/embedding-based semantic, dense/hybrid and reranking settings against the corresponding Chroma index. Retrieved chunk IDs, queries, scores and source hashes are recorded in the frozen JSON packet. Validated parent expansion preserves complete source tables for Python calculations. The CLI writes HTML, diagnostic Markdown and JSON under `data/reports/`. Report generation needs a configured embedding provider and compatible index; it does not require model prose generation. The landing map remains a fast source-table snapshot. Map filters do not change the full-campaign report scope. Opening balances mean account balances at opening in USD, not current balances, net new deposits or revenue.

The current input corpus is synthetic Markdown under `data/corpus/`. Real PDF, Word, PowerPoint, Excel/CSV and database ingestion is explicitly future work; the app does not yet ingest real client files.

The separate eleven-section analytical RAG report remains available with:

```powershell
python -m campaign_hub report --campaign TX-CHK-001
```

For a faster deterministic report retaining source wording, without model prose generation:

```powershell
python -m campaign_hub report --campaign TX-CHK-001 --extractive
```

These two analytical modes use real embeddings, Chroma retrieval, and cited evidence. The optional model can suggest concise wording; unsupported paraphrases fall back to verbatim source evidence. KPI variance arithmetic is performed in Python. Analytical outputs are under `data/reports/`: `<campaign>.md`, `<campaign>-technical.md`, and `<campaign>.json`. Outputs are never automatically re-ingested. Use `client-report` for the final presentation packet.

Report sections: Executive Summary, Goal Achievement Analysis, KPI Performance Review, Performance Drivers, Audience Insights, Channel Insights, Recommendations, Lessons Learned, Suggested Next Steps, Presentation Storyline, and Source Citations.

Inputs: campaign brief, success plan, KPI results, historical campaigns, and best practices. Source performance reports contain KPI actuals; they are distinct from newly generated reports. Missing evidence yields a partial report with explicit gaps, not invented findings. Confidence is evidence coverage, not probability of truth.

## Ask, inspect, and evaluate

```powershell
python -m campaign_hub ask --campaign TX-CHK-001 --question "What were the objectives?"
python -m campaign_hub evaluate --smoke --extractive
python -m campaign_hub evaluate --full
python -m pytest -q
```

Reranking downloads `cross-encoder/ms-marco-MiniLM-L-6-v2` on first use. Enable with `--rerank` or the UI toggle; the experiment matrix tests both states. Full evaluation may take considerable time on CPU. Run artifacts under `data/runs/` contain actual results/errors, not example scores. A retrieval-only experiment marks generation as skipped. Add `--judge` for a separate local model support judgment; source/number validation alone does not prove semantic faithfulness, and a model judge is not human verification.

Actual **RAGAS faithfulness, passage context precision and reference-claim context recall** are available through the optional [RAGAS assessment workflow](docs/ragas-assessment.md). Install `requirements-ragas.txt`, then run `python -m campaign_hub evaluate --ragas --ragas-limit 1` with the selected generation/embedding providers. This assesses real generated answers and preserves exact contexts/references and judge identity in saved JSON/CSV artifacts. The evaluation dashboard module is retained for development and is not exposed in client navigation. It never substitutes document-ID overlap scores for RAGAS judgments. Local Ollama inference needs no paid API; missing judgments remain unavailable.

The opt-in [90% quality target workflow](docs/quality-target.md) adds reference-based factual correctness, actual per-passage verdicts, complete-case coverage and judge calibration checks. `--focus-context` tests question-specific evidence sections without changing live defaults. The first local judge failed negative controls, so its high raw relevance scores are explicitly untrusted; the target remains unmet. Use a separately configured judge that passes controls before interpreting a quality score.

Default model settings use local Ollama. `CIH_GENERATION_PROVIDER` and `CIH_EMBEDDING_PROVIDER` can select the hosted Groq/CPU profile; OpenAI answer generation is also optional. See the cloud quickstart for server secrets. `CIH_OLLAMA_URL`, `CIH_GENERATION_MODEL`, and `CIH_EMBEDDING_MODEL` configure the selected models. Model/chunker changes use isolated compatible indexes.

## Project layout

```text
app.py                 Streamlit entry point
src/campaign_hub/
  synthetic_data/      Seeded corpus and manifest validation
  ingestion/           Source parsing and path validation
  chunking/            Fixed, section-based and embedding-based semantic chunking
  embeddings/          Local embedding client and cache
  generation/          Local structured generation client
  vectordb/            Persistent Chroma indexes
  retrieval/           Dense/BM25 fusion
  reranking/           Local cross-encoder
  reporting/           KPI calculations, claims, report rendering
  langgraph/           Executable report workflow
  evaluation/          Gold metrics and experiment runner
  ui/                  Streamlit interface
data/corpus/           Synthetic Markdown sources
data/evaluation/       Gold questions
docs/                  Architecture and course methodology
tests/                 Automated tests
```

See [architecture](docs/architecture.md), [methodology](docs/methodology.md), and [evaluation status](docs/evaluation-results.md).
