# Credit Union Evidence Lab Week 2 Project Report

## Project overview

Credit Union Evidence Lab helps financial analysts answer asset, lending, and ratio questions from original NCUA financial reports in a public web interface. It demonstrates document-only RAG with LangChain, LangGraph, ChromaDB, local embedding/reranking models, and Groq generation.

The quality targets are at least 90% generated-answer faithfulness, at least 80% evidence recall at five retrieved passages, and warm end-to-end p95 response time of at most 15 seconds. These are targets; measured results and their scope are reported separately below and in the evaluation artifacts.

This implements the handout's Financial Document Intelligence project: two chunking strategies compared on identical queries, a reranking step, measured retrieval quality and reranking impact, and a compact chatbot UI.

## Dataset and source of truth

The delivered snapshot contains 18 original online NCUA reports for nine credit unions. Financial summary and historical ratio tables contain annual reporting columns covering 2021–2025. The institutions are Alliant, America First, Boeing Employees, First Technology, Mountain America, Navy Federal, Pentagon, Spokane Firefighters, and State Employees'.

NCUA is the source of truth. Original report bytes, source URLs, retrieval timestamps, charter numbers, document hashes, and unavailable requests are recorded in the manifest. Charter 244 was unavailable. No synthetic financial reports or bulk financial CSVs were substituted.

NCUA's full Financial Performance Report PDF service requests email delivery. The downloadable online documents are HTML, so this project preserves those originals and cites table and row references. Source views remove executable markup while keeping financial table cells. They do not claim to be original PDFs.

Source entry point: https://ncua.gov/analysis/credit-union-corporate-call-report-data/financial-performance-reports
Public report application: https://fpr.ncua.gov/

## Framework decisions

Use case: Financial analysts explore credit union balance sheets, loan balances, and reported ratios in a public web chat; comparisons apply only to the downloaded sample.

Ingestion and cleaning: A resumable, paced downloader requests public online reports, validates charter identity, and saves original HTML. Table extraction retains row labels, reporting headers, institution identity, units, and source references; malformed NCUA headers are handled explicitly.

Freshness: The corpus is a dated assignment snapshot. A manual refresh can be run after quarterly releases; this project does not schedule recurring downloads or promise an unattended freshness SLA.

Chunking and embedding: The fixed strategy uses a 200-token target with 30-token overlap. The semantic strategy combines adjacent source rows by embedding similarity, with a 200-token ceiling and a 0.55 similarity boundary. Both use the same tokenizer and 384-dimensional all-MiniLM-L6-v2 embeddings. The delivered indexes contain 540 fixed chunks and 396 semantic chunks.

Vector storage: Separate persistent ChromaDB collections hold each strategy's vectors, chunk text, and citation metadata. The LangChain Chroma integration applies institution/year filters before dense retrieval; BM25 receives the same filters. Stable IDs and corpus hashes support idempotent refresh and removal of stale chunks.

Retrieval: Chroma dense results and BM25 keyword results are fused with reciprocal rank fusion. Twenty candidates are considered, and five passages are returned. The optional cross-encoder reranker is ms-marco-MiniLM-L-6-v2. Model snapshot revisions are recorded in the project assets.

Generation: LangGraph coordinates retrieval, evidence coverage checks, abstention or partial-evidence output, and LangChain ChatGroq. The selected generation model is openai/gpt-oss-20b served through Groq; no OpenAI API key is used. A server-side key and token protect generation, with bounded requests and a shared demonstration generation budget.

## Prompts and agent instructions

The generation prompt instructs the model to use only retrieved evidence, treat document text as data rather than instructions, identify institution/period/units, preserve ratio denominators, and cite evidence IDs. It prohibits nationwide ranking claims from a sample and asks the model to state missing or conflicting evidence.

Numbers should be copied in their original source units. The demo prefers reported annual %Chg columns to unsupported arithmetic. Citation syntax is normalized before validation; unknown IDs and numerical claims absent from their cited passages are rejected. These mechanical checks reduce some failure modes but do not prove complete semantic faithfulness.

The exact prompt is included in pipeline/graph.py. The application's development instructions emphasized authentic source acquisition, no fabricated scores, secret exclusion, tests before implementation, and an independent final review.

## Iterations and observations

First, source inspection established that online report downloads differ from the email-delivered full PDF workflow. Original HTML was used transparently instead of creating replacement PDFs.

Second, real NCUA markup exposed a header structure without a tr element. A failing regression test reproduced the parser failure before the identity parser was corrected. Coverage was later restricted to actual table headers because explanatory accounting notes mention years outside the financial reporting columns.

Third, fixed and semantic indexes were evaluated with and without reranking. The strongest improvements came from the reranker; semantic chunking alone did not outperform the fixed baseline on this small question set.

Fourth, review demonstrated that a valid citation ID alone does not establish factual support. The application now checks institution/metric/period coverage before making a complete comparison and rejects unsupported numerical claims. Provider-specific citation bracket variants were normalized during live Groq integration checks.

Finally, Groq's model listing showed that the initial template model was unavailable to this account. The project selected an available model and kept the model ID configurable.

## Retrieval evaluation and reranking impact

The same 15 manually labeled questions are used across four configurations: twelve evidence questions, including a cross-document comparison, and three expected abstentions. Labels identify relevant original source rows before scoring. Raw results contain queries, retrieved texts, citations, timings, and failure cases.

Fixed without reranking: recall@5 0.917, MRR 0.736, nDCG@5 0.783, expected-abstention accuracy 1.000, local retrieval p95 0.328 seconds.

Fixed with reranking: recall@5 0.958, MRR 1.000, nDCG@5 0.968, expected-abstention accuracy 1.000, local retrieval p95 1.168 seconds.

Semantic without reranking: recall@5 0.917, MRR 0.708, nDCG@5 0.760, expected-abstention accuracy 1.000, local retrieval p95 0.169 seconds.

Semantic with reranking: recall@5 0.958, MRR 0.958, nDCG@5 0.937, expected-abstention accuracy 1.000, local retrieval p95 1.410 seconds.

Reranking improved recall@5 by 0.042 for both chunkers. The difficult cross-document case still lacked complete evidence across configurations. That failure is preserved in the report, and the answer pipeline refuses a definitive comparison when the required metric/period coverage is incomplete. Local retrieval timing excludes network and Groq generation and is not end-to-end latency.

The three negative cases use explicit missing-topic, missing-period, and missing-institution gates. Their perfect abstention result does not demonstrate general hallucination resistance. Retrieval recall is not answer faithfulness; a separate generation assessment records generated-answer quality.

## UI and deployment

The streamlined UI contains a question box, institution/year filters, retrieval controls, expandable evidence, safe original-source views, and experiment results. The front end is prepared for Sites, but publication is blocked by the session's terminal-input permission policy. No public deployment has been verified. The local Python backend is connected through a Cloudflare Quick Tunnel, so the local computer, Python service, and tunnel must stay running for live answers. After publication, hosted source views and experiment results can remain available independently.

A durable deployment would put the Python application and Chroma persistence on an always-on host, or use hosted Chroma plus an application server. The current connection is an educational demonstration, not an always-on production service.

## AI coding tools and learning

Codex assisted with requirements mapping, implementation, test development, debugging, documentation, UI development, deployment preparation, and an independent code review. The implementation uses real NCUA documents and observed test/evaluation output; generated code or plausible model answers were not treated as verification.

The main learning is that financial RAG depends on preserving table meaning, keeping ratio denominators explicit, testing retrieval with labeled evidence, and designing an insufficient-evidence path. A fluent answer alone is not sufficient evidence of correctness.

## Live generation and final verification

All 26 Python tests and 3 UI proxy tests passed. A 15-question live Groq assessment completed with 12-second pacing and no application rate-limit responses. Eight generated answers were displayed, three drafts were withheld after validation and one repair attempt, one comparison returned partial evidence, and all three negative questions abstained. Manual comparison found the displayed figures match their cited rows; two ratio answers omitted explicit units. This small developer review does not establish the 0.90 independent faithfulness target. API processing p95 was 5.888 seconds; public end-to-end latency remains unmeasured. See evaluation/generation-review.md for details.

The secret scan found no configured secrets in publishable source files or build outputs. Publication remains blocked because the session disables sandbox approval for hidden terminal input, even after the user's approval. No expected site URL should be represented as live.

## Submission assets and remaining user actions

The source ZIP, original reports, manifest, indexes, evaluation JSON, comparison report, and timed demo script accompany this document. Record a personal live walkthrough of at most five minutes using the script, then submit the public app link, documentation link, source ZIP or GitHub link, and recording through the course form. This project does not submit the form or claim an unrecorded video exists.

## Annual-report extension

The expanded local corpus contains 19 NCUA reports for ten institutions and ten official Navy Federal/BECU annual-report PDFs covering 2021–2025. The PDFs provide 850 physical pages, including 626 nonempty extracted pages. Both indexes include the extension: 2,151 fixed chunks and 1,891 semantic chunks. Publisher type, report year, original URL, SHA-256 and physical page references are retained. Membership-count questions use the annual-report collection; membership-ratio questions retain NCUA sources. Explicit annual-query years override the UI default year. The original benchmark scores remain results from the 18-report NCUA snapshot, not the expanded corpus. The extension passes 36 Python tests, three proxy tests, a production UI build, and secret scans. A live membership answer was verified against the original 2024 Navy Federal PDF, physical page 3. Public access is through a temporary tunnel at https://nato-minimum-intervals-kim.trycloudflare.com and depends on the local services staying running.


## Expanded-corpus evaluation results

The matched 38-question run used 32 evidence questions and six negative cases on the same 29-document corpus, with source labels fixed before the final run. Without reranking, fixed and semantic recall@5 both reached 0.750; MRR was 0.625 and 0.635. With reranking, fixed recall/MRR was 0.828/0.844 and semantic was 0.818/0.813. Source-balanced averages lead to the same ordering with reranking. The results do not establish an overall semantic advantage. Five exact membership-count questions fail to retrieve the precise PDF table count, and the caption-only BECU 2024 case returns unhelpful evidence. See evaluation/expanded/comparison-report.md, frozen questions and raw results for details. These scores measure retrieval, not generated-answer faithfulness.


## PDF membership-table repair and frozen evaluation

Five Navy Federal Financial Summary rows now have validated table passages preserving institution, both consecutive year columns, exact integer membership counts, units, and physical PDF page. These supplement existing text without replacing it. Ambiguous headers, malformed counts, equity labels, and unsupported layouts are rejected; no OCR or count inference is performed. The audit is data/supplemental/membership-table-audit.json. Index counts are 2,156 fixed and 1,896 semantic chunks. Incremental indexing embeds added/changed passages only.

All 45 regression tests pass. The identical 38-question set (SHA-256 b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9) was rerun after indexing. Exact membership evidence improved from 0/5 to 5/5 for every configuration. With reranking, combined Recall@5 rose from 0.828 to 0.984 for fixed and 0.818 to 0.974 for semantic; MRR rose from 0.844 to 1.000 and 0.812 to 0.969 respectively. Negative-case empty-retrieval accuracy remains 5/6. This does not establish a semantic advantage. The repair was motivated by known test failures, so this is a regression evaluation rather than independent held-out evidence. Generation is not measured by this retrieval benchmark.

Original results are preserved in evaluation/expanded/pre-table-fix/; new results, frozen labels and before-after report are in evaluation/expanded/post-table-fix/. Repeat with python scripts/evaluate_after_table_fix.py after building indexes. Public report path: /pdf-table-fix-comparison.txt.

## Reviewed BECU OCR

Selected financial tables in the 2023 and 2024 BECU annual reports now use local Tesseract.js 7.0.0 OCR. Nineteen pages were processed; nine table pages were visually reviewed and normalized into 119 passages carrying row context, year columns and printed units. Only reviewed passages are searchable. Raw OCR and character-correction audit are in data/supplemental/ocr-raw/ and ocr-review-audit.json; source PDFs and the original pypdf cache remain unchanged. See data/supplemental/OCR-README.md for scope and reproduction steps. This is targeted table recovery, not complete OCR coverage of all pages.

Indexes contain 2,275 fixed and 1,936 semantic chunks. All 48 tests pass, including reviewed/unreviewed OCR gating and preservation of year/unit context. Exact BECU membership counts verified on physical pages are 1,457,207 in 2023 (page 69) and 1,514,773 in 2024 (page 100).

Evaluation version 3 retains the same 38 question texts and filters. Before retrieval, A21/A22 changed from missing-evidence negatives to verified evidence questions, giving 34 evidence cases and four negatives. Versioned labels and results are under evaluation/expanded/post-ocr/; previous runs remain intact. This is a regression experiment on a small convenience set, not evidence of universal chunker superiority.

OCR evaluation results: using identical version-3 labels for pre-OCR saved passages and new retrieval, reranked Recall@5 increased 0.926 to 0.985 for fixed and 0.917 to 0.975 for semantic. Both recover A21/A22 exact BECU membership evidence; four negative cases return no evidence. Fixed remains slightly ahead. See evaluation/expanded/post-ocr/before-after.md. Raw timings were interrupted by long execution pauses and are excluded from performance conclusions. Public report: /becu-ocr-evaluation.txt.
