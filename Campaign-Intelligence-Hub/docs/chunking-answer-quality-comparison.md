# Chunking comparison on generated answers

Historical 122-source corpus measurements. The current corpus contains130 sources; these results are preserved for provenance and do not certify the expanded corpus. See [requirements pack](requirements-corpus.md).

Evaluated the same 30 questions using Ollama llama3.2:3b answers and calibrated OpenAI gpt-4.1-mini judgments. Hybrid retrieval, candidate k20, returned k5, no reranking and no context focusing were held constant. Source corpus, references, generation prompt, evaluation versions and embedding profile match. The section-based baseline was retained; fixed and semantic are new sequential executions.

## Best observed answer quality

Best observed reference-answer F1 across all 23 supported questions: semantic.

The primary measure was specified before running the new methods: average model-judged reference F1 across all supported questions, counting genuine refusals as zero. Missing judgments on answered questions make that primary comparison incomplete. Conditional faithfulness is shown with its denominator; it does not reward methods simply for refusing difficult questions.

| Chunking | Reference F1 across all supported | Answered | Faithfulness among assessed answers | Passage precision | RAGAS ranked precision | Context recall | Unsupported refusals | Answer p95 seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed | 22.0% | 16/23 | 99.0% (16/23) | 51.3% | 75.0% | 100.0% | 7/7 | 99.18 |
| section | 30.5% | 18/23 | 100.0% (18/23) | 34.8% | 76.1% | 100.0% | 7/7 | 62.79 |
| semantic | 33.5% | 20/23 | 100.0% (20/23) | 38.0% | 77.5% | 97.8% | 7/7 | 43.58 |

## Corpus shape and tradeoffs

The supported set has 18 campaign-source questions and five questions requiring the longer learning guides. This distribution can favor a method that works well on short campaign documents.

| Chunking | Source group | Supported cases | Answered | Reference F1 with refusals zero |
|---|---|---:|---:|---:|
| fixed | campaign_sources | 18 | 14 | 25.8% |
| fixed | learning_guides | 5 | 2 | 8.0% |
| section | campaign_sources | 18 | 15 | 31.6% |
| section | learning_guides | 5 | 3 | 26.4% |
| semantic | campaign_sources | 18 | 17 | 30.0% |
| semantic | learning_guides | 5 | 3 | 46.0% |

## Interpretation and limits

- Passage precision counts useful passages, whose size differs across chunkers. A large fixed chunk can contain the needed fact and many irrelevant sentences while still being counted useful; this is why reference correctness and coverage are shown too.
- Faithfulness measures whether an answer is supported by its passages, not whether it answers the question completely. F1 compares against curated references and is a model judgment, not independently verified human accuracy.
- The earlier retrieval-only document-precision leader was semantic/hybrid without reranking. That diagnostic is a different outcome from generated-answer quality.
- These are single executions on source-derived synthetic examples. No confidence interval, repeated-run variance or universal winner is established. The section baseline was measured earlier, with its precision subsequently reassessed on its saved answers; all current identities and sample contracts match.
- Timing excludes judge calls. Configurations ran sequentially with varying cache states and machine load, so timing differences are descriptive rather than controlled causal effects.
- All 90 case/configuration pairs are present. Per-case errors, abstentions and missing judgments remain in the artifacts; no unfavorable numeric result was selectively retried or dropped. The app default was not changed by this experiment.

## Reproducible evidence

[Protocol](evaluation/chunking-quality-protocol.json), [summary](evaluation/chunking-answer-quality-summary.json), [all 90 records](evaluation/chunking-answer-quality-results.json), and [CSV](evaluation/chunking-answer-quality-results.csv). Each record includes actual generated answer, exact source-labeled contexts, references, model identity, calibration and metric errors. API keys remain private.
