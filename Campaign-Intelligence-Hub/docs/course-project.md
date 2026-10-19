# Week 2 course project

## Business problem and deliverable

Analysts combine prospective campaign goals with results, historical lessons, and guidance to produce client-ready reports. This application makes that process reproducible with a synthetic banking corpus and auditable retrieval.

The final deliverable is a standalone HTML Campaign Performance Report with comparison charts, insights underneath, goals/progress, learnings, recommendations, next steps, measurement notes and citations. It uses real Chroma retrieval, validated parent-document expansion and deterministic Python calculations. The original eleven-section analytical RAG report and storyline remain available through the CLI. Supporting pages expose retrieval/evaluation results. The landing workspace automatically displays the selected client's campaign geography and same-client historical standing.

The complete [implementation audit](implementation-status.md) records all 102 checklist items, including eight explicit future-work items. This is a synthetic local demonstration, not a production client-data deployment.

## Demonstration sequence

1. Inspect one linked campaign in `data/corpus/`; confirm common campaign ID and distinct brief/plan/results/deck purposes.
2. Build fixed-size, section-based and embedding-based semantic Chroma collections with the CLI or setup button; hosted startup prepares them automatically.
3. Generate TX-CHK-001's report and inspect the target-versus-actual table.
4. Expand cited evidence and verify a numerical statement against the source.
5. Compare all three chunkers in Retrieval Explorer, then vary dense/hybrid search while keeping the same campaign and question.
6. Enable real reranking, then inspect the changed ranks and scores.
7. Run the smoke matrix; inspect actual MRR, precision, recall, completeness proxies, errors, and latency.
8. Request an unknown campaign or unsupported fact and demonstrate abstention or explicit gaps.

## Interpretation

This small synthetic dataset demonstrates architecture and experiment mechanics, not real-world model quality. Similar wording and source-derived gold facts may inflate retrieval results. Section-based chunking follows headings; embedding-based semantic chunking uses sentence/unit cosine-distance breakpoints. They are separate controls and indexes. Cite each finding, separate historical analogies from current results, and distinguish measured evidence from proposed tests.

The local profile uses Ollama embeddings and generation; the hosted demo uses CPU embeddings and the owner's Groq free-tier API. Hardware, quotas, memory, model size, and cold downloads affect latency. No customer records are used.
