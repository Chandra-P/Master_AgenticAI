# Week 2 course project

## Business problem and deliverable

Analysts combine prospective campaign goals with results, historical lessons, and guidance to produce client-ready reports. This application makes that process reproducible with a synthetic banking corpus and auditable retrieval.

The final deliverable is an eleven-section Campaign Performance Report, not just a chatbot. Supporting pages let reviewers inspect retrieval and measured evaluation results. The report compares goals and KPIs, summarizes observed audience/channel patterns, presents recommendations and lessons, and includes a five-slide presentation storyline and source bibliography.

## Demonstration sequence

1. Inspect one linked campaign in `data/corpus/`; confirm common campaign ID and distinct brief/plan/results/deck purposes.
2. Build fixed and semantic Chroma collections with the CLI or setup button.
3. Generate TX-CHK-001's report and inspect the target-versus-actual table.
4. Expand cited evidence and verify a numerical statement against the source.
5. Compare fixed/dense against semantic/hybrid in Retrieval Explorer.
6. Enable real reranking, then inspect the changed ranks and scores.
7. Run the smoke matrix; inspect actual MRR, precision, recall, completeness proxies, errors, and latency.
8. Request an unknown campaign or unsupported fact and demonstrate abstention or explicit gaps.

## Interpretation

This small synthetic dataset demonstrates architecture and experiment mechanics, not real-world model quality. Similar wording and source-derived gold facts may inflate retrieval results. Business-heading chunking is a structural semantic baseline. Cite each finding, separate historical analogies from current results, and distinguish measured evidence from proposed tests.

All embeddings and generation run through free local APIs. Hardware, memory, model size, and cold downloads affect latency. No external financial recommendations or customer records are used.
