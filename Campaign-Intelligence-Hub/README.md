# Campaign Intelligence Hub — RAG workspace

Ask questions about campaign knowledge, retrieve source evidence, and compare how
chunking changes what is retrieved. The active application is a RAG solution:

**Sources → chunks → local embeddings → Chroma → dense/hybrid retrieval → optional reranking → context → cited answer.**

Report generation, KPI dashboards, presentation export, and historical-comparison
workflows are no longer part of the active app or CLI. Original campaign reports
remain useful **input documents** in the knowledge base. Obsolete report code,
export assets, dependencies and historical score bundles have been removed.
The active LangGraph workflow explicitly routes retrieval to a source-validated
answer or refusal, and records retrieval and end-to-end answer latency.

## Run locally on Windows

Keep Ollama running and download the models once:

```powershell
ollama pull llama3.2:3b
ollama pull embeddinggemma:latest
```

From this project directory, use Python3.12 or newer. On this workstation the
project environment is already installed. For a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Generate/validate the source corpus and build all three actual indexes:

```powershell
.\.venv\Scripts\python.exe -m campaign_hub generate
.\.venv\Scripts\python.exe -m campaign_hub validate
.\.venv\Scripts\python.exe -m campaign_hub index --chunking all
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8504
```

Open http://127.0.0.1:8504. Initial indexing may take several minutes on a CPU.
Later builds reuse the embedding cache. Index directories include the corpus
identity so expanded sources do not overwrite historical collections. Changing
sources, embedding model, or chunking configuration requires compatible indexes.
Stop the server with Ctrl+C. Calling the environment's Python directly avoids
PowerShell activation-policy problems.

## The four workflows

### Ask Questions

Search the **entire knowledge base** by default, or choose **Selected campaign**
for a binding campaign scope. Enter a question and select **Find evidence**.
Answers use retrieved passages and exact source citations. Unsupported claims
are withheld; source-validated wording is deliberately conservative rather than
free-form report writing. No report arithmetic or presentation template is run.

Automatic metadata classification defaults to local Ollama. Combined filters
support campaign ID, client, campaign type, region, year, reporting period and
document type. Values inside one field use OR; different fields use AND. Manual
constraints intersect inferred constraints; conflicts stop the search. A general
question without recognized metadata terms needs no classification call.
Unsupported paraphrases and shared ALL/GLOBAL values can use manual controls.

### Analyst View

Inspect manual, inferred, scope, routing and effective filters. Expand retrieved
chunks to see source text, metadata, chunk IDs and ranking scores. Scores are
labeled dense/BM25/fusion/reranking signals, not confidence probabilities. Edits
hide stale evidence, and no inference runs until explicit submission.

### Chunking Lab

Choose one of the new long learning guides and click **Inspect indexed chunks**.
The same canonical source appears with its actual fixed-size, section-based and
embedding-based semantic chunks. Expand chunks to see token lengths, verified
source spans, overlap and boundary metadata. Unknown spans remain unknown.

- **Fixed-size:** up to500 cl100k_base tokens with50-token overflow overlap.
- **Section-based:** heading boundaries, with the same overflow bounds for long sections.
- **Semantic:** sentence/unit embedding cosine-distance boundaries at the configured percentile,
  with bounded overflow windows. This is actual embedding-based segmentation.

Then enter a query and choose **Compare retrieved evidence**. All three indexes
receive the same query, metadata filters, retrieval method and reranking setting.
The selected source is for chunk inspection; retrieval comparison searches the
filtered corpus rather than secretly restricting results to that source.
Semantic chunking does not necessarily improve every query.

### Evaluation

Current document precision, document recall, MRR and latency are computed only
from question cases on the matching corpus/model/chunker configuration. Report
cases and old bundled scores are excluded. The page shows measured-case coverage
and errors; a one-case smoke run is explicitly incomplete.

The new guide questions are labeled **development** examples, separate from
legacy held-out cases. These are synthetic teaching data, not independent real
client validation. Retrieval precision/recall do not measure answer faithfulness.
Faithfulness remains unavailable unless separately assessed on generated answers.

```powershell
# Six retrieval configurations, one held-out question each, no generation
.\.venv\Scripts\python.exe -m campaign_hub evaluate --smoke
# All new demonstration questions across six configurations
.\.venv\Scripts\python.exe -m campaign_hub evaluate --full --split development
# All eligible held-out question cases; add --generated for actual answers
.\.venv\Scripts\python.exe -m campaign_hub evaluate --full
```

Use --include-reranking to add both reranking states. The optional cross-encoder
requires its downloaded model files. Current artifacts are in data/runs/rag/latest;
historical raw runs are excluded. Optional `evaluate --ragas --ragas-limit 1`
assesses actual generated answers after judge calibration. Use
`--judge-provider openai --judge-model gpt-4.1-mini` only with a private owner key.
Ollama remains the default. Failed calibration is shown explicitly in Evaluation;
it cannot produce reportable scores. A smoke assessment is not a full benchmark.

## Current answer-quality result

The fixed 30-case benchmark on the expanded 130-source corpus reached **87.3% reference F1**, up from **36.9%** for its baseline. It answered 22/23 supported questions and refused all 7 unsupported controls. The default is now semantic chunking with hybrid retrieval and eight chunks; Ollama remains the answer provider. Narrow factual answers use verified source extraction, while broader questions use the local model.

This is a development benchmark, not independent certification. Complex-question F1 averaged 51.5%, and useful-passage precision remains below target. See [complete results and limitations](docs/expanded-quality-results.md).

## Corpus

The original 110 source documents and their hashes are preserved. The expanded
corpus contains 130 documents: the original 110, twelve original learning guides,
and eight new [requirements-pack sources](docs/requirements-corpus.md). The original guides include long
playbooks, cohesive policies, heading-free mixed-topic notes, and troubleshooting
FAQs with identifiers, tables, exceptions and boundary-sensitive facts. They
exist to make chunking behavior inspectable, rather than padding source text.
Each has a curated development question and expected source evidence. Check the
manifest and Chunking Lab for actual token/chunk counts.

Current local Ollama indexes contain **180 fixed**, **580 section-based**, and
**788 semantic** chunks. New-source inspections are recorded
in [corpus validation](docs/evaluation/requirements-corpus-validation.json). For the preserved consent-recovery playbook alone the counts are
**3 / 7 / 22**, illustrating different boundary decisions rather than proving one
method is universally better. All new guide chunks passed canonical source-span
and token-bound checks.

Historical 122-source [retrieval measurements](docs/evaluation/pure-rag-retrieval-comparison.csv)
and [paired reranking analysis](docs/evaluation-results.md) compare the same
questions across chunkers and reranking states. The benchmark includes ambiguous,
multi-document and unsupported cases. Newly authored synthetic examples are not
independent blind validation. Unsupported questions have undefined retrieval
relevance rather than artificial zero scores.

The [course framework](docs/course-project.md), [requirements matrix](docs/requirements-matrix.md)
and [local submission document](docs/submission/Campaign_Knowledge_RAG.docx)
separate implemented features from measured quality targets. The local judge's
[failed calibration](docs/evaluation/current-judge-controls.json) means local
faithfulness scores remain unavailable.

Local hand-in assets include a [three-page overview](docs/submission/Campaign_Knowledge_RAG.docx)
and [2:06 edited walkthrough](docs/submission/Campaign_RAG_Walkthrough.mp4).
The video uses actual UI captures with text narration; it is labeled as edited
footage. The owner requested local document delivery, so no Google Doc or course
submission was created. The observed 67.53-second answer exceeded the proposed
60-second sample ceiling; a warm p95 pass has not been demonstrated.

## Models and credentials

The completed [three-chunker answer-quality comparison](docs/chunking-answer-quality-comparison.md)
contains 90 case/method records. Semantic had the highest observed reference F1
across all 23 supported questions, counting refusals as zero: **33.5%**, versus
**30.5% section-based** and **22.0% fixed-size**. It answered **20/23** supported
questions; all three methods correctly refused all seven unsupported controls.
The observed advantage came from the longer learning-guide questions. This is a
single-run synthetic comparison; the app's default chunker was not changed.

The completed [OpenAI-judged quality evaluation](docs/openai-quality-results.md)
is the section-based baseline and uses Ollama answers with an explicit OpenAI judge across 30 cases. Faithfulness
was 100% on 18 answered supported cases; five supported cases were refused.
RAGAS rank-weighted context precision was 76.1%, useful-passage precision 34.8%,
and context recall 100%. All seven unsupported controls returned the canonical
refusal. Reference factual-correctness F1 was 38.9% on assessed answers, and
observed answer p95 was 62.79 seconds. These results do not meet all stated
quality targets. The key remains in private ignored settings.

The evaluator now preserves the exact source IDs and text visible to generation.
Precision explanations are bounded by provider token limits rather than an
unnecessary character cap; binary verdicts remain strictly validated. Prior
diagnostic runs are archived and excluded from current results.

Ollama is the default for classification, embeddings and answers; no API keys are
required for that profile. The configured local defaults are llama3.2:3b and
embeddinggemma. CIH_OLLAMA_URL selects the local endpoint.

OpenAI remains an optional explicit **Classification provider** or sidebar
**Answer provider**, defaulting to gpt-4.1-mini for that alternative. Configure
OPENAI_API_KEY in the process environment or ignored .streamlit/secrets.toml.
Never paste keys into source or widgets. OpenAI classification sends the question
and candidate metadata; OpenAI answers also send retrieved passages. There is no
automatic cloud fallback. Embeddings remain unchanged when selecting an answer provider.

Configuration names: CIH_GENERATION_PROVIDER, CIH_GENERATION_MODEL,
CIH_EMBEDDING_PROVIDER, CIH_EMBEDDING_MODEL, CIH_CLASSIFICATION_PROVIDER,
CIH_CLASSIFICATION_MODEL, CIH_OLLAMA_URL. The app reads process environment and
private Streamlit secrets; a project .env is not loaded automatically.

## CLI examples

```powershell
.\.venv\Scripts\python.exe -m campaign_hub ask --question "What are the tracking validation procedures?"
.\.venv\Scripts\python.exe -m campaign_hub ask --campaign TX-CHK-001 --question "What were the objectives?"
.\.venv\Scripts\python.exe -m campaign_hub ask --classify --question "Find performance reports for Texas campaigns in 2026."
.\.venv\Scripts\python.exe -m pytest -q
```

Supported commands are generate, validate, index, ask and evaluate. Prior report,
client-report and compare commands have been removed. No authentication or real
client-data tenancy is claimed; the supplied corpus is fictional teaching data.
