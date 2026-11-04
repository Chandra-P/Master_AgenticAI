# Campaign RAG requirements completion

User authorization: implement the remaining Week 2 requirements and remove unwanted reporting code. Preserve Ollama as default and all source corpus documents. OpenAI remains optional; never store keys.

1. Remove report-generation modules and obsolete report-only tests/assets. Move synthetic-data helpers out of reporting; preserve corpus bytes.
2. Run question answering through a genuine LangGraph retrieval / generation-and-source-validation / refusal graph. Record retrieval and end-to-end latency.
3. Add ambiguous, multi-document and unsupported benchmark cases with documented source gold. Compare identical questions across chunkers and reranking states.
4. Support calibrated, current-corpus generated-answer RAGAS measurements and optional OpenAI judge. Failed calibration or unavailable judgments must remain visible, never fabricated.
5. Refresh project framework, requirements matrix, measured comparison / failure analysis, freshness SLA, latency targets and submission materials.
6. Run full tests, source-integrity and credential checks, then independent review. Restart local demo.

Ruling: the campaign knowledge base is the handout's allowed bring-your-own use case. SEC/Pinecone/Jev choices in the financial reference are examples, not additional mandatory product features.
Ruling: preserve source performance reports as corpus inputs; remove output-report generation. Work in the existing checkout to preserve the user's approved uncommitted pure-RAG changes.

## Progress

- Implementation started; cleanup, benchmark authoring and assessment support are independent delegated workstreams.
- Removed report runtime and assets, preserved all 122 source files; local full suite passed 131 tests before final dead-code pruning.
- Review fixes: failed calibration is visible even with zero result rows; currentness validates scoring/calibration versions; generated and retrieval timing remain separate.
- Ruling: complete the 30-case paired held_out matrix; retain compatible development baseline separately rather than spend another full reranking matrix on demonstration-only examples. Local reranking costs about 12 seconds per query.
- Actual local judge calibration failed three negative controls. No cloud judging has been authorized or performed for this benchmark; faithfulness remains unavailable.
- User chose to keep submission documentation local. Google Drive folder creation was rejected by automatic approval review and was not retried or bypassed.
- Live browser verified expected consent gate CR-217, applied TX/year/document-type constraints, 3/7/22 indexed guide chunks and explicit failed-judge warning. One answer took 67.53 seconds, exceeding the proposed 60-second sample ceiling; no p95 achievement is claimed.
- Completed 360 current held_out retrieval rows (30 cases x 12 configurations), zero errors, plus 72 identity-compatible development baseline rows. Saved complete profiles, paired deltas and failure analysis.
- Final frozen-code verification: 131 non-live tests passed, 3 existing RAGAS adapter deprecation warnings, 157.85 seconds. Corpus validation passed; API-key pattern scan found no matches in changed files or DOCX XML.
- Local three-page DOCX visually verified and 2:06 edited walkthrough fully decoded and sampled. No Google Doc, cloud judging, course submission, commit or push performed.

## Authorized OpenAI evaluation follow-up

- Owner configured the OpenAI key in ignored server secrets and authorized evaluation; Ollama remains the answer provider/default. No keys were printed or added to source.
- Fixed evaluator context mismatch after an actual OpenAI NLI trace showed campaign identity missing from text-only judge passages. Generation and evaluation now share exact source IDs and text; assessment version 3, calibration version 2.
- Removed an unnecessary 160-character explanation validator after it rejected a valid binary precision verdict with a 249-character reason. Kept binary 0/1 validation and provider token limits; precision prompt version 4. Rejudged precision for all 23 supported cases, preserving every original answer and unaffected metric with provenance. Both diagnostic executions are archived.
- Completed 30 cases; precision/recall measured on all 23 supported cases. Faithfulness 100% on 18 answered cases; five supported refusals; all seven unsupported controls correctly refused. Rank-weighted context precision 76.1%, useful-passage fraction 34.8%, context recall 100%, reference F1 38.9%, observed answer p95 62.79 seconds. Targets remain unmet.
- Final non-live suite: 133 passed, three existing RAGAS adapter deprecation warnings. Additional precision tests: two passed; corpus validation passed. Independent read-only review found no important issues.
- Saved docs/openai-quality-results.md and identity-bearing data artifacts. Restarted local app. Native Google Doc remains intentionally uncreated; no commit or push.

## Three-chunker generated-answer comparison

- User authorized fixed and semantic evaluations against the existing compatible section baseline. Frozen protocol saved before new runs; Ollama answers, OpenAI judge, hybrid retrieval, no reranking, candidate20/final5, same corpus/questions/prompts.
- Completed 90 case/method records with zero execution errors. All profiles and references were verified against the protocol; independent arithmetic checks passed. All 90 current records load in the Evaluation view.
- Primary predeclared mean reference F1 across all23supported questions (genuine refusals0): semantic33.48%, section30.48%, fixed21.96%. Supported answers20/23,18/23,16/23 respectively. All three correctly refused all7unsupported questions.
- Semantic advantage was strongest on five long-guide questions (46% versus section26.4% and fixed8%). Section slightly led on the18campaign-source questions. Single execution and synthetic/source-derived data; no statistical/universal superiority claimed.
- Public report: docs/chunking-answer-quality-comparison.md; protocol, raw90JSON/CSV and summary under docs/evaluation. Independent reviewer caught incomplete-competitor winner and protocol-validation gaps in the one-off export script; both were fixed before export.
- App default chunker and model were not changed. No source/runtime changes in this experiment, no commit/push, no API keys in artifacts.
