# Requirements evidence corpus

The current library has **130 synthetic Markdown sources**: 110 original campaign/shared documents, 12 original learning guides and eight new CL-640 evidence-pack documents. All previous source bytes and question records are preserved. No hosted generation or API keys were used to author or index this pack.

## Source coverage

| Source | Requirement exercised | Shape | Fixed / section / semantic chunks |
|---|---|---|---|
| [GLOBAL-requirements-01](../data/corpus/learning_guide/GLOBAL-requirements-01.md) | Measurement ambiguity, units, missing values and numeric table evidence | playbook | 2 / 5 / 9 |
| [GLOBAL-requirements-02](../data/corpus/learning_guide/GLOBAL-requirements-02.md) | Occurrence versus arrival, maturity and time-zone qualifications | cohesive_policy | 2 / 2 / 12 |
| [GLOBAL-requirements-03](../data/corpus/learning_guide/GLOBAL-requirements-03.md) | Archived policy and historical effective scope | cohesive_policy | 2 / 2 / 10 |
| [GLOBAL-requirements-04](../data/corpus/learning_guide/GLOBAL-requirements-04.md) | Current policy, supersession and distinct approval roles | playbook | 2 / 6 / 10 |
| [GLOBAL-requirements-05](../data/corpus/learning_guide/GLOBAL-requirements-05.md) | Payload identity, checksum holds and launch readiness | playbook | 1 / 6 / 10 |
| [GLOBAL-requirements-06](../data/corpus/learning_guide/GLOBAL-requirements-06.md) | Receipt timeouts, idempotency, exception paths and decision tables | troubleshooting | 1 / 5 / 7 |
| [GLOBAL-requirements-07](../data/corpus/learning_guide/GLOBAL-requirements-07.md) | Heading-free topic changes, stale evidence and mixed incidents | mixed_notes | 2 / 2 / 12 |
| [GLOBAL-requirements-08](../data/corpus/learning_guide/GLOBAL-requirements-08.md) | Source trust, untrusted record instructions, masked evidence and access limits | cohesive_policy | 2 / 2 / 11 |

The canary scope is fictional CL-640. Revision one is explicitly archived, while revision two governs releases on or after 2026-10-01. These scoped policies do not supersede unrelated consent or attribution sources. Source metadata carries the evidence-pack ID, effective date, version and active/superseded status.

## Exercises and provenance

Thirteen new cases in `data/evaluation/questions.json` are development examples: eight single-source questions, three cross-document questions and two unsupported controls. They include exact source facts and section citations. The full library now has 25 development cases, 30 legacy held-out cases and three calibration cases. The new sources and exercise gold were authored together; this is not independent blind evaluation.

The cross-document exercises combine balance meaning with timing policy, release approvals with checksum-mismatch reconciliation, and a missing-checksum hold with the required contents of a masked-sample request. Unsupported controls ask for a real account identifier and randomized causal lift, neither of which exists in the corpus.

## Local validation

All eight new sources passed exact canonical span and 500-token chunk-bound checks across all three indexes. Current full index counts are **180 fixed, 580 section and 788 semantic**. The original 122 documents and all prior question records are preserved; deterministic regeneration is tested.

Thirty-nine development retrieval executions covered 13 questions across three chunkers. Each chunker achieved document recall 1.0 on the 11 supported new exercises. Unsupported cases have no relevant gold documents and were excluded from that recall mean. No generated-answer correctness, faithfulness or refusal accuracy is implied. Full records: [validation artifact](evaluation/requirements-corpus-validation.json).

## Try it locally

Open Chunking Lab, choose `GLOBAL-requirements-01` to compare table and heading boundaries, or `GLOBAL-requirements-07` for topic transitions without headings. Inspect each strategy, then compare retrieved evidence with the same query and settings. Use corpus-wide scope so GLOBAL documents are eligible.

Example: “Who approves a current CL-640 release, and who reconciles a partner status checksum mismatch before further transmission?” Inspect revision two and the receipt protocol together. For a version-precedence exercise ask: “Is revision one the current approval rule for CL-640 releases?”

## What remains unproven

Expanding a corpus does not establish the 80% reference-F1 goal or other quality/latency thresholds. Historical evaluation artifacts describe the prior 122-source corpus and are not current quality results. The app rejects stale corpus-specific scores. Run a new generated-answer comparison and use fresh independent held-out questions before making broader quality claims. The previous local submission document/video and source ZIP describe the earlier corpus and need refreshing before resubmission.

Subsequent answer evaluation on this 130-source corpus reached 87.3% reference F1 on the fixed 30-case benchmark; see [expanded results](expanded-quality-results.md). This does not change the development-only status of the new exercises or certify unseen quality.
