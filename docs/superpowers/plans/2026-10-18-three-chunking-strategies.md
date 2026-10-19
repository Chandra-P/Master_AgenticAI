# Three Chunking Strategies Implementation Plan

> Execute inline with superpowers:executing-plans. Use regression tests and verification before completion.

**Goal:** Deliver fixed-size, section-based, and embedding-based semantic chunking with an honest comparison and checklist audit.

**Architecture:** Preserve the current structural algorithm as `section` and make `semantic` mean sentence/unit embedding cosine-distance breakpoints. Keep exact source spans, bounded chunks, table protection, and per-strategy/model/configuration Chroma identities. Default to section-based retrieval for the established client-report workflow.

**Scope:** The user's approved three-way comparison and remaining-requirements audit. Continue using LangChain embedding interfaces, Chroma, free local/hosted model profiles, direct mail/display attribution and source-validated HTML reports. Do not adopt instructions, paid services, or claimed results from peer documents.

## Tasks

- [x] Add failing tests for semantic topic boundaries, unchanged-heading independence, source-span fidelity, tables, long/Unicode inputs, invalid vectors, and parameter identity.
- [x] Implement sentence/unit cosine segmentation using the configured LangChain embedder, a recorded 65th-percentile threshold, and 500-token bounds with 50-token overflow overlap.
- [x] Rename the existing heading strategy to section-based; make defaults, CLI, hosted bootstrap, UI controls and explorer support all three modes.
- [x] Include chunker configuration in index names/manifests and evaluation identities, rejecting legacy semantic indexes/results.
- [x] Expand the dense/hybrid and reranking on/off matrix to twelve configurations and show actual measurements.
- [x] Build all three CPU-model indexes, run meaningful retrieval/report smoke checks and the held-out comparison; keep missing faithfulness values unavailable.
- [x] Audit peer deliverable topics and all 102 checklist items; document current gaps and results without copying peers' metrics.
- [x] Run the full regression suite, perform focused review, then push verified changes and check the hosted deployment.

## Review Focus

Semantic boundaries must depend on embeddings rather than headings. Every returned character must be source-backed. Large tables must not disappear or bypass model/token budgets. Model or chunker changes must not reuse incompatible indexes/results. Hosted startup must not silently fall back to structural chunking when semantic embedding fails.

## Verification ledger

- Full regression suite: 91 passed. Actual CPU indexes: fixed 130, section 490, semantic 445 chunks; each generated a validated ten-chart default-campaign report.
- Final runner-version-6 held-out experiment: 324 rows, zero execution errors; 36 complete and 24 partial analytical reports. Faithfulness was not measured. Raw rows and configuration means are archived under `Campaign-Intelligence-Hub/docs/evaluation/three-chunking-*`.
- Read-only review caught multi-section citation and leading partial-section attribution issues. Regression tests reproduced both; conservative span resolution and versioned score invalidation fixed them. Follow-up review reported no remaining Critical/Important finding in that scope.
- Implementation pushed as `426b542`. Incognito hosted verification selected Embedding-based semantic and generated the validated report, displaying all ten charts, findings, citations and HTML download.
- Checklist counted mechanically: 94 IMPLEMENTED / 8 FUTURE WORK. The deliverable audit retains the distinction between feature coverage and production/factual readiness.
