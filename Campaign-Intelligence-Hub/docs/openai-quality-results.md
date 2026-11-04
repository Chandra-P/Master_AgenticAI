# OpenAI judged Ollama answer evaluation

Historical 122-source corpus measurements. The current corpus contains130 sources; these results are preserved for provenance and do not certify the expanded corpus. See [requirements pack](requirements-corpus.md).

This document describes the **section-based baseline**. The subsequent
[three-chunker comparison](chunking-answer-quality-comparison.md) contains all
90 case/method records and the answer-quality ranking.

Measured on 25 October 2026 using the current 122-document synthetic corpus. Ollama llama3.2:3b generated every answer. OpenAI gpt-4.1-mini only judged the saved answers and evidence. Local default providers were not changed.

All four matching-source-ID relevance controls passed. A separate diagnostic accepted a supported source quotation and rejected an invented profit claim.

## Measured scores

| Metric | Mean | Measured supported cases |
|---|---:|---:|
| Faithfulness of generated answers | 100.0% | 18/23 |
| RAGAS rank-weighted context precision | 76.1% | 23/23 |
| Useful retrieved passage fraction | 34.8% | 23/23 |
| RAGAS context recall | 100.0% | 23/23 |
| Reference factual correctness F1 | 38.9% | 18/23 |

Completed 30/30 cases with 0 execution errors. Answer coverage: 18/23 supported questions. Unsupported refusal accuracy: 7/7.

RAGAS context precision is rank weighted. It can be high when the first passage is relevant even though most other passages are irrelevant. The useful-passage fraction is shown separately to avoid calling rank quality ordinary passage precision. Refused supported questions have no answer faithfulness score; they remain in answer-coverage denominators.

Observed end-to-end answer latency: median 27.06s, p95 62.79s, maximum 75.64s. This is a single 30-case execution, not a controlled warm-load SLA certification. Judge time is excluded from these answer timings.

## Evaluation correction and provenance

The initial diagnostic dropped source IDs from judge context. RAGAS decomposed an exact objective quote into campaign-specific statements, then could not verify the campaign identity in unlabeled passage text. Generation had received the source ID. The corrected evaluator shares the generation source serializer and passes exactly the same source ID and text. Scorer version 3, precision prompt version 4 and calibration version 2 reject incompatible artifacts. The initial five-case run was archived, not silently replaced with claimed results. No source text, answer prompt or retrieval configuration was changed to improve scores.

[Diagnostic trace](evaluation/openai-context-diagnostic.json) records the original and corrected judgments plus a negative unsupported-claim control. The source-context correction was measured in a fresh full run with new Ollama generations. Precision was then rejudged for every supported case because the previous parser discarded valid verdicts when explanations exceeded 160 characters. Only that explanation limit was removed; binary verdict validation and output-token limits remain. The same saved answers and contexts were used for all precision reassessments. Faithfulness, recall and factual correctness retain their original measurements and timestamps, recorded in each row. Both prior executions were archived; unfavorable numeric results were not selectively retried or dropped.

## Interpretation

These are model judgments on synthetic and source-derived examples, not independent human validation or production certification. Faithfulness among answered cases must be read with answer coverage. The stated targets are 90% faithfulness and 80% passage relevance; a high rank-weighted precision alone does not establish that the passage relevance target is met. The existing complete-set quality gate remains available in data/runs/quality/latest/quality-summary.json and treats missing claim judgments as incomplete.

[Full results](evaluation/openai-quality-results.json) contain actual responses, exact source-labeled contexts, references, controls, identities and per-metric errors. [CSV](evaluation/openai-quality-results.csv) and [summary](evaluation/openai-quality-summary.json) are separate from retrieval-only document metrics. API keys remain in private ignored settings.
