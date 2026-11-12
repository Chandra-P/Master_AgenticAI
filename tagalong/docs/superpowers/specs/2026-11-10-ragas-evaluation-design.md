# Ragas Evaluation Design

## Intent

Extend Tagalong's existing Group Fit RAG evaluation with an opt-in Ragas scoring pass over synthetic live Pinecone retrieval and OpenAI assessment cases. The purpose is to measure grounding, response relevance, and whether relevant group evidence is retrieved, beyond the current deterministic citation checks and one-case ablation.

## Current state

`backend/scripts/evaluate_group_fit.py` already creates in-memory synthetic plans, uses temporary plan-scoped Pinecone namespaces, calls the live Group Fit endpoint and OpenAI, verifies expected source retrieval/citation, records latencies, and deletes its synthetic vectors. It writes timestamped JSON and Markdown artifacts. It does not currently depend on Ragas or compute Ragas scores.

## Approved approach

Add Ragas as a separate evaluation dependency group and an opt-in scoring pass in the existing evaluator. Preserve the current live synthetic harness as the data source; do not use production plans, the production database, or production namespaces. Keep normal CI and the normal backend runtime free of Ragas model calls. The existing credential-free tests will cover evaluation-row construction and scoring result serialization using fakes; the live command will require explicit evaluator credentials and clearly report model-call/cleanup status.

## Evaluation data and metrics

For each eligible live case, retain the exact evidence sent to the Group Fit model, split into Pinecone-retrieved source contexts and other prompt evidence. Build a Ragas single-turn sample from the synthetic option/query, prompt evidence, normalized generated findings, and a scenario-specific reference answer. Score:

- Faithfulness: whether generated assessment claims are supported by supplied evidence.
- Answer relevancy: whether the assessment addresses the proposed option and group-fit question.
- Context precision and context recall: whether Pinecone-retrieved evidence is relevant to, and covers, the synthetic reference facts.

Report Ragas scores separately from deterministic checks (expected verdict, valid citations, retrieval-hit rate, and ablation effect). Do not present an LLM judge score as proof of correctness; record the evaluator model/version, metric errors, per-case scores, latency, and aggregate means. Do not add a pass/fail quality threshold until a human-reviewed baseline is established.

## Safety and cost boundaries

- Synthetic content only; no real user or production plan data.
- Only random evaluation namespaces and `eval-` source IDs are created or deleted.
- Ragas is opt-in and absent from application startup, API runtime dependencies, and regular CI.
- The live scoring command must make its extra model calls explicit and write timestamped reports beside current evaluation artifacts.
- Cleanup remains in `finally`; report cleanup failures without suppressing them.

## Acceptance criteria

1. A normal credential-free pytest run verifies Ragas dataset/sample construction and artifact serialization without importing or calling the live judge.
2. The opt-in evaluator includes actual prompt evidence and generated Group Fit output, plus synthetic references, in Ragas input.
3. Pinecone-only contexts are scored separately from authoritative Postgres facts, Notes, recent chat, and user-supplied option text.
4. Reports preserve current deterministic and ablation metrics and add per-metric/per-case Ragas scores, aggregate means, and an honest error/skip state.
5. Ragas is only an evaluation dependency; standard API installs and CI do not run paid/live Ragas calls.
6. Documentation includes the command, required environment variable names (never values), cost/privacy scope, and metric limitations.

## Risks and limits

Ragas metrics are model-based estimates, not ground truth. Four synthetic cases are too small to claim general quality. Context precision/recall depend on carefully authored synthetic reference facts, and faithfulness depends on capturing the exact evidence supplied to the model. If the selected Ragas release changes its metric API, the adapter must pin the version and cover its mapping with tests.
