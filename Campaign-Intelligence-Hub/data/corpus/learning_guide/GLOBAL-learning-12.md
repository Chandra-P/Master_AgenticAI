---
campaign_id: GLOBAL
campaign_name: Knowledge source troubleshooting FAQ
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional troubleshooting about knowledge source troubleshooting
  faq; authored for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-12
document_shape: troubleshooting
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Knowledge source troubleshooting FAQ

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Why can an old answer cite a familiar document?

A document identifier names a source but does not establish which revision supplied the answer. The fictional knowledge service stores the manifest identity, source checksum, chunking configuration, embedding model identity, and retrieval settings with a result. If an author revises a policy under the same identifier, the old chunks may still exist in a recoverable collection. Their presence is useful for historical investigation but does not make them current evidence. The analyst checks the current manifest and source bytes before presenting a cached answer as a fresh response. A filename or a recent modification time alone is not enough to establish compatibility.

## KS-663 mismatch

KS-663 rejects a cached retrieval result when its source checksum differs from the current manifest, even if the document identifier is unchanged.

The check applies before a result is displayed as current. Preserve rejected result metadata for diagnosis without mixing its scores into the new run. The service may explain that an older run exists, but it must identify its original corpus and configuration. A stale answer can contain perfectly fluent prose and syntactically valid citations while supporting a rule that the author has since replaced. Fluency and citation shape cannot substitute for source identity.

| Diagnostic code | Observed mismatch | Required response |
|---|---|---|
| KS-663 | Source checksum changed | Reject cached current result |
| KS-664 | Embedding model changed | Rebuild compatible vectors |
| KS-665 | Chunk boundaries changed | Use matching chunk collection |
| KS-666 | Question case set changed | Recompute evaluation identity |

## Exception for historical investigation

Exception KS-670 permits opening an old collection to investigate what evidence an earlier answer used. The interface labels its historical corpus identity and does not present the result as current. A reviewer may need to compare the earlier policy text with a revision to understand a past decision. This use preserves the original source checksum and configuration rather than silently substituting current text under old citations. The exception does not allow old evaluation scores to populate a new corpus dashboard. Historical reproducibility and current correctness answer different questions, and the record must make clear which one is being examined.

## Why did adding a source change rankings?

New sources can introduce both relevant evidence and plausible distractors. Sparse term statistics can change, dense neighborhoods can become more crowded, and reranking can select a different final set from the candidate pool. A new ranking is not automatically an improvement or a regression. Inspect the retrieved text, the filters, and the question's expected evidence. A shared policy may legitimately outrank a campaign brief for a policy question while being irrelevant to a campaign-specific target question. Evaluation should therefore disclose its case set and scope instead of treating one aggregate score as proof that every kind of question improved.

## What if a citation points to the wrong passage?

First verify that the cited chunk exists in the selected collection and matches the current source checksum. Then inspect whether its text supports the associated claim. A citation can be valid as an identifier yet irrelevant to the claim. A paragraph about delivery retries does not establish an enrollment window merely because both belong to the same campaign library. The analyst should distinguish missing retrieval, incorrect context selection, and unsupported answer synthesis. Those failure stages suggest different repairs. Adding more context indiscriminately can worsen the problem by surrounding a small relevant fact with attractive but unrelated instructions.

## Reproducing the comparison

Record the question, effective metadata constraints, corpus identity, chunk strategy, embedding identity, retrieval mode, candidate count, final count, and reranker setting. Preserve the returned chunk identifiers and source text so another analyst can inspect the evidence. Compare methods using the same question and binding scope. A campaign-specific run should not be compared with a corpus-wide run as though only the chunking method changed. This FAQ offers development cases for exploring those controls. They are curated examples used during implementation, not a held-out benchmark, and no measured semantic advantage is claimed merely because the examples were designed to expose boundary behavior.

## Reproduction trace

The synthetic cache exercise starts with a policy source, an indexed collection, and a cited answer saved under the original manifest. An author then changes the policy's recovery gate while keeping its document identifier. The current manifest now contains a different checksum. Opening the saved answer as current must trigger KS-663 before any quality score or answer is presented as fresh. The investigator can still open the historical record under KS-670 and inspect the exact earlier text. The difference between those routes is visible in the corpus identity, not inferred from the answer's writing style.

A second trace leaves the source bytes unchanged but changes the embedding model. The collection compatibility check rejects vectors built under the previous model identity. Merely updating a configuration label would misrepresent the stored vectors. A third trace changes chunk boundaries while retaining the source and embedding model. Chunk identifiers, citation spans, and retrieval results belong to the boundary configuration that produced them. The test checks that an old chunk result is not silently relabeled with the new strategy. These scenarios distinguish source invalidation from model and algorithm invalidation.

The final exercise adds development questions and recomputes the evaluation identity. Historical results retain their original case list and denominator. A missing current run produces an unavailable result, not an inherited score with a new title. Reviewers inspect the cases that were actually run and the cases excluded by kind or scope. This keeps demonstration examples useful without pretending they are independent evidence of general quality. The teaching objective is reproducibility of a concrete retrieval comparison and honesty about measurement coverage, including the possibility that a carefully designed example exposes a weakness in the chosen strategy.
