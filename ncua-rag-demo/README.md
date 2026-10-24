# Credit Union Evidence Lab

A document-only financial RAG demo built with LangChain, LangGraph, ChromaDB, local MiniLM embeddings and reranking, and Groq answer generation. The small public UI offers questions, institution/year filters, original source tables, and measured retrieval experiments.

## Corpus

The original benchmark snapshot contains 18 original NCUA online HTML reports for nine credit unions, with annual columns covering 2021–2025. NCUA's full FPR PDF workflow requests email delivery, so this project uses downloadable original online financial summaries and historical ratios instead. Original bytes and SHA-256 hashes are retained. Citations identify HTML tables and rows, not fictional PDF page numbers.

The sample includes Navy Federal, Pentagon, Boeing Employees, First Technology, Alliant, State Employees', Spokane Firefighters, America First, and Mountain America. It is not the national universe. Charter 244 was unavailable; the manifest records that gap rather than substituting data.

## Report downloads with Git LFS

The annual-report PDFs are stored with Git LFS in the parent Master_AgenticAI repository. After cloning, run `git lfs install` and `git lfs pull` from the repository root before using the supplemental report corpus. The included manifests preserve original public source URLs and SHA-256 hashes.

## Run locally

Use Python 3.12 and Node.js 24 or later. In this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py index
python run.py evaluate
python run.py export
```

The reports are already included. `python run.py download` downloads missing reports and resumes the manifest; report requests are sequential and limited to 30 per UTC day by this demo. It does not submit email requests. Model weights download from Hugging Face on first use.

Create an ignored `.env` in the project root from `.env.example`, setting `GROQ_API_KEY`, `GROQ_MODEL`, and a random `RAG_BACKEND_TOKEN`. Never put secrets in public files. The configured Groq model is `openai/gpt-oss-20b`, served by Groq; no OpenAI API key is required. Model availability depends on the account, and the ID remains configurable.

```powershell
python run.py serve
```

The Python API listens on `127.0.0.1:8765`. The server uses local persistent Chroma collections; no Chroma Cloud account is required for this backend. It never exposes Chroma management operations publicly. Groq generation requires the backend token, an API key, and the evidence gate. Without Groq credentials it shows retrieval-only results.

In `site/`, install the dependencies and start the UI using the included starter scripts:

```powershell
npm install
npm run dev
```

Set the site's ignored `.env.local` to `RAG_BACKEND_URL=http://127.0.0.1:8765` and the same backend token. The public deployment uses hosted runtime configuration instead. Backend URL/token values are not browser inputs and are not shipped to visitors.

## Architecture

1. `pipeline/acquire.py` validates institution identity and preserves original NCUA reports plus a resumable manifest.
2. `pipeline/extract.py` converts table rows to LangChain Documents, retaining financial labels, period columns, units, source tables, and row numbers.
3. `pipeline/chunk.py` compares tokenizer-bounded fixed chunks (200 tokens, 30 overlap) with embedding-similarity semantic groups (200-token ceiling, similarity boundary 0.55).
4. `pipeline/index.py` uses the LangChain Chroma integration and persistent ChromaDB collections for each strategy. Stable chunk IDs, model identity, and corpus hashes support refreshes and remove stale vectors.
5. `pipeline/retrieve.py` combines Chroma dense results and BM25 using reciprocal rank fusion, retrieves 20 candidates, and optionally reranks to five with a cross-encoder.
6. `pipeline/graph.py` uses LangGraph to retrieve, check institution/metric/period coverage, abstain or report partial evidence, then call LangChain ChatGroq. Unknown citations and unsupported numeric claims fail closed. These checks do not substitute for evaluating full answer faithfulness.
7. The Sites UI proxies requests to the Python API, displays cited source passages, and publishes the source library and experiment results.

## Evaluation

See `evaluation/comparison-report.md`, `evaluation/results.json`, and the 15 labeled questions in `evaluation/questions.json`. Four configurations use the same corpus, queries, candidates, and labels. The retrieval experiment found recall@5 of 0.917 without reranking and 0.958 with reranking for both chunkers. The cross-institution case still misses required evidence, so the application blocks definitive comparisons when coverage is incomplete.

Targets: at least 0.80 evidence recall@5, at least 0.90 generated-answer faithfulness, and warm end-to-end p95 at most 15 seconds. Measured retrieval latency excludes network and generation. Any separate generation assessment is stored in `evaluation/generation-results.json`; retrieval scores must not be reported as answer accuracy.

## Public deployment and operation

The Sites UI is publicly accessible after a successful deployment. The current demo connects to a local Python backend using an outbound Cloudflare Quick Tunnel; live search and answers therefore require this computer, the Python service, and the tunnel to remain running. The source library and saved experiment results remain hosted independently. This is a demonstration connection, not an always-on production backend.

For a durable deployment, run this Python backend on an always-on host with a persistent disk for ChromaDB, or configure a hosted Chroma server and keep Python inference on an application host. Change the server-side `RAG_BACKEND_URL`; no UI rewrite is required. Keep the token secret and preserve request limits. The current shared demo limits requests and Groq generations per server lifetime; it does not promise a production billing cap.

## Verification

```powershell
python -m pytest tests -q
cd site
node --test tests/proxy.test.mjs
npm run build
```

Regression coverage includes malformed NCUA HTML, identity validation, metadata preservation, semantic boundaries, Chroma persistence and filtering, stale chunk cleanup, unsupported numerical claims, comparison coverage, invalid payloads, and safe source rendering.

## Submission assets

`submission/project-documentation.md` and the native Google Doc contain the project overview, framework decisions, actual data, prompts, iterations, evaluation, and observations. `submission/demo-script.md` provides a walkthrough of at most five minutes. The source ZIP excludes API keys, environments, and temporary files. A personal live demo recording and submission through the course form remain user actions unless a recording is explicitly included in the final deliverables.

## Expanded sources

The current local project contains 19 NCUA reports for ten institutions, plus ten official annual-report PDFs (Navy Federal and BECU, 2021–2025). Supplemental originals, SHA-256 hashes, source URLs and one-based physical PDF page references are in data/supplemental/. The page text includes 626 nonempty pages out of 850 physical pages; selected BECU financial tables now have reviewed OCR; other image-only pages remain unprocessed. PDF table reading order must be checked against the original page. Institution definitions and units may differ from NCUA figures.

Membership questions use annual reports; ordinary financial questions retain the NCUA collection. Fixed and semantic chunkers process the supplemental passages, and semantic groups retain physical page boundaries. Existing evaluation scores belong to the original 18-report NCUA snapshot. They have not been remeasured for the expanded corpus.

To reacquire the annual sources, install requirements-sources.txt and run python scripts/collect_annual_reports.py, then python run.py index and python run.py export. Initial PDF text extraction used pypdf 6.10.0. A separate reviewed OCR cache now augments selected BECU tables. Cached PDFs are reused.


## Expanded retrieval evaluation

A separate 38-question study on the 29-document corpus is saved in evaluation/expanded/. It compares both chunkers with and without reranking, with source-balanced results and exploratory paired uncertainty estimates. It does not demonstrate an overall semantic advantage. Original benchmark files and the baseline Experiments screen remain intact. See evaluation/expanded/comparison-report.md for measured results and limitations.


## PDF membership-table repair and frozen evaluation

Five Navy Federal Financial Summary rows now have validated table passages preserving institution, both consecutive year columns, exact integer membership counts, units, and physical PDF page. These supplement existing text without replacing it. Ambiguous headers, malformed counts, equity labels, and unsupported layouts are rejected; no OCR or count inference is performed. The audit is data/supplemental/membership-table-audit.json. Index counts are 2,156 fixed and 1,896 semantic chunks. Incremental indexing embeds added/changed passages only.

All 45 regression tests pass. The identical 38-question set (SHA-256 b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9) was rerun after indexing. Exact membership evidence improved from 0/5 to 5/5 for every configuration. With reranking, combined Recall@5 rose from 0.828 to 0.984 for fixed and 0.818 to 0.974 for semantic; MRR rose from 0.844 to 1.000 and 0.812 to 0.969 respectively. Negative-case empty-retrieval accuracy remains 5/6. This does not establish a semantic advantage. The repair was motivated by known test failures, so this is a regression evaluation rather than independent held-out evidence. Generation is not measured by this retrieval benchmark.

Original results are preserved in evaluation/expanded/pre-table-fix/; new results, frozen labels and before-after report are in evaluation/expanded/post-table-fix/. Repeat with python scripts/evaluate_after_table_fix.py after building indexes. Public report path: /pdf-table-fix-comparison.txt.

## Reviewed BECU OCR

Selected financial tables in the 2023 and 2024 BECU annual reports now use local Tesseract.js 7.0.0 OCR. Nineteen pages were processed; nine table pages were visually reviewed and normalized into 119 passages carrying row context, year columns and printed units. Only reviewed passages are searchable. Raw OCR and character-correction audit are in data/supplemental/ocr-raw/ and ocr-review-audit.json; source PDFs and the original pypdf cache remain unchanged. See data/supplemental/OCR-README.md for scope and reproduction steps. This is targeted table recovery, not complete OCR coverage of all pages.

Indexes contain 2,275 fixed and 1,936 semantic chunks. All 48 tests pass, including reviewed/unreviewed OCR gating and preservation of year/unit context. Exact BECU membership counts verified on physical pages are 1,457,207 in 2023 (page 69) and 1,514,773 in 2024 (page 100).

Evaluation version 3 retains the same 38 question texts and filters. Before retrieval, A21/A22 changed from missing-evidence negatives to verified evidence questions, giving 34 evidence cases and four negatives. Versioned labels and results are under evaluation/expanded/post-ocr/; previous runs remain intact. This is a regression experiment on a small convenience set, not evidence of universal chunker superiority.

OCR evaluation results: using identical version-3 labels for pre-OCR saved passages and new retrieval, reranked Recall@5 increased 0.926 to 0.985 for fixed and 0.917 to 0.975 for semantic. Both recover A21/A22 exact BECU membership evidence; four negative cases return no evidence. Fixed remains slightly ahead. See evaluation/expanded/post-ocr/before-after.md. Raw timings were interrupted by long execution pauses and are excluded from performance conclusions. Public report: /becu-ocr-evaluation.txt.
