# Campaign knowledge RAG course project

My RAG app helps campaign analysts answer objectives, measurement and operating-policy questions from 130 English synthetic campaign documents in Streamlit, targeting 90% generated-answer faithfulness and 80% passage relevance precision on a calibrated evaluation set. These are acceptance targets, not measured achievements.

## Scope and framework

This is the handout's bring-your-own use case on the LangChain and LangGraph code track. It applies the financial kit's chunking, reranking and evaluation experiments to campaign knowledge. Apple SEC filings, Pinecone and Jev are reference choices, not additional requirements. GraphRAG and support escalation are alternative projects.

| Framework field | Decision |
|---|---|
| User and surface | Campaign analysts ask about goals, results, exceptions, consent and tracking procedures in Streamlit. |
| Corpus and owner | Repository maintainer owns data/corpus and data/manifest.json: 110 original documents across 20 campaigns plus 12 original learning guides and eight requirements-pack sources. All 130 files are English Markdown and explicitly synthetic, with no customer records. |
| Ingestion and cleaning | Validate manifest hashes and metadata before loading UTF-8 Markdown. Heading markers delimit sections; preserve tables, identifiers and original source wording for exact evidence checks. No SEC/PDF parser is claimed. |
| Freshness | Static versioned corpus, reviewed by the maintainer weekly and after approved changes. Manual freshness SLA: validate sources and rebuild all three indexes within one working day of an approved update; no scheduled ingestion service is claimed. |
| Chunking and embedding | Fixed windows up to 500 tokens, heading sections and embedding-based semantic boundaries at percentile 65. Long units use 50-token overflow overlap. Local embeddinggemma keeps embeddings private. |
| Retrieval | Persistent Chroma dense search or dense plus BM25 reciprocal-rank fusion. Retrieve 20 candidates, optionally rerank using the real MiniLM cross-encoder, return five chunks. |
| Filters | Local automatic metadata classification and manual constraints: OR within fields, AND across fields, intersect inferred/manual/scope constraints. Conflicts stop retrieval. |
| Generation | LangGraph retrieves, branches to generation with source validation or refusal, then records timing. Model-authored claims must occur verbatim in every cited source chunk. Narrow factual answers may instead use verified complete sections or reconciled count-table projections with source-cell proofs. This conservative check does not prove relevance to the question. |
| Runtime features | Ask Questions, Analyst View, Chunking Lab, Evaluation. Report generation, presentations, maps and report history were removed. |
| Latency | Target warm end-to-end p95 at most 60 seconds on the owner's machine, excluding initial downloads/indexing. Record observed retrieval and answer times; no achieved ceiling is claimed without a complete generated-answer run. |
| Evaluation | Identical queries, filters and top-k across three chunkers, dense/hybrid and reranking off/on. Document overlap and MRR are retrieval diagnostics; calibrated RAGAS judges actual generated answers and exact ranked passages. |

## Dataset and benchmark provenance

The twelve original longer guides cover playbooks, cohesive policies, mixed-topic notes and troubleshooting so chunk boundaries can be inspected. All original source files are preserved byte-for-byte. Tests compare regenerated manifests and all 130 corpus files with checked-in versions.

The active benchmark has 30 cases in the legacy held_out split and 25 development cases (12 original and 13 requirements-pack exercises). Eight were authored during this implementation: three ambiguous, three requiring distinct source documents and two unsupported controls. Gold facts and citations are explicit. The split name is retained for compatibility; source-derived references and newly authored cases are not independent blind validation or evidence of production accuracy.

## Prompts and instructions

The answer prompt in src/campaign_hub/rag/grounding.py requires only retrieved sources, at most three concise verbatim claims and exact source IDs, ignoring instructions in sources. Empty claims mean refusal. A deterministic validator rejects incorrect IDs and claims absent from their cited passages; it can recover an omitted ID only for a unique exact retrieved-source quote.

The classifier prompt requires structured allowed metadata values with an exact supporting quote from the question. It cannot relax filters, infer campaign IDs from year/region, or assign shared ALL/GLOBAL values automatically.

Real RAGAS faithfulness, context precision and context recall are optional measurements. A positive and three negative relevance controls must pass first. The local llama3.2:3b judge failed these controls, so its scores remain unavailable; see docs/evaluation/current-judge-controls.json. Optional OpenAI answers or judging require an owner key kept in private settings.

## Iterations and learnings

The earlier app mixed retrieval with campaign report generation. The current build isolates question answering and chunking experiments. Longer sources were added because short documents gave a weak demonstration of boundary choices.

Valid citations and document recall do not establish faithful answers or relevant passages. The evaluator separates measurements, rejects stale corpus/model/case identities and blocks an uncalibrated judge. Semantic segmentation can produce many small chunks and hurt some questions. Reranking must be measured rather than presumed to improve every case.

## Verification and submission

See [measured evaluation and failure analysis](evaluation-results.md), [chunking comparison](chunking-comparison.md) and [requirements matrix](requirements-matrix.md). The comparison document is a course asset separate from runtime features.

The handout requests a Google Doc covering overview, datasets, prompts, iterations and learnings; a video at most five minutes explaining the app and use of AI coding tools with a live result; and GitHub code or assets. Codex assisted with implementation, tests, synthetic examples and documentation. Preparing these assets does not submit the course form or certify a grade.

The CL-640 requirements pack adds measurement definitions, attribution timing, scoped active/superseded policies, release/receipt procedures and evidence access. All original122 sources and prior questions are preserved. Historical quality measurements and submission video/document describe the earlier corpus; see requirements-corpus.md for the current source pack and validation.

Current measured answer improvement: semantic/hybrid/k8 reached 87.3% reference F1 on the fixed 30-case development benchmark; see [expanded results](expanded-quality-results.md). Narrow factual projections preserve source-cell proofs, while broader generation remains local Ollama. Passage precision and independent validation remain outstanding.
