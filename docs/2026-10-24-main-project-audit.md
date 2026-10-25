# Main workspace audit — 2026-10-24

Scope: all six project folders on local `main`. AI inference defaults to local
Ollama, without an OpenAI API key. Optional hosted Campaign profiles are retained;
the effective local Campaign settings use Ollama.

## Fixes

- Week 1: installable Ollama/web-search dependencies and refreshed lockfile;
  notebook project-path resolution from either the workspace or notebook folder;
  configurable local model URL/name; corrected setup instructions.
- Week 2: converted the support viewer to the notebooks' local models and
  `shopeasy-local-rag` namespace, with index dimension validation and constrained
  structured filters. All notebook/template defaults now select installed models
  `embeddinggemma:latest` and `llama3.2:3b`. Removed the unused OpenAI dependency,
  aligned Streamlit requirements, and corrected README filename casing.
- KidSpark: repaired the local runtime by creating its own environment with the
  already-declared Plotly/pandas/Streamlit dependencies; added a reproducible
  lockfile. No application behavior changed.
- Dhumsharath: portable install/API development scripts, Windows native build
  dependencies, a pinned pnpm version and equivalent strict build-script policy,
  and local Vite defaults. Required sign-in is preserved; authenticated gameplay
  still needs its existing Clerk configuration, independently of AI models.
- NCUA: local Ollama generation and batched embeddings, model-separated vector
  collections, an explicit index migration check, optional reranking, truthful
  backend/model metadata for assessment, a longer bounded inference proxy
  timeout, and a frontend JSON-error type fix. Existing historical benchmark
  outputs and original corpus are preserved.
- The live NCUA check also exposed a citation parser bug: a correct citation
  after a sentence's period was rejected. Validation now associates it with
  that sentence, while later unsupported numeric claims still fail closed.

## Verified checks

| Project | Result |
| --- | --- |
| Campaign Intelligence Hub | 113 tests pass; real local embedding (768 dimensions) and chat smoke pass |
| KidSpark | 46 tests pass, including Streamlit interactions and persisted progress |
| Week 1 | 2 offline tests pass; every notebook code cell passes with Ollama; final interactive cell supplied `quit` |
| Week 2 | 10 tests pass; metadata/hybrid notebooks pass end to end; support viewer startup, all three retrieval strategies, and local cited generation pass |
| Dhumsharath | 25 tests pass; full TypeScript checks and production builds pass |
| NCUA | 55 Python tests pass in its freshly installed project environment, including three citation regressions; 4 proxy tests, frontend TypeScript and production build pass |

Windows sandbox restrictions caused stalled temporary-directory and subprocess
checks; successful runs used writable test directories and the required execution
permissions. Tests were not weakened to accommodate sandbox failures.

Nonblocking upstream warnings remain: the RAGAS LangChain wrapper is deprecated;
the Dhumsharath client bundle exceeds Vite's advisory chunk-size threshold; and
Vinext cannot statically classify every dynamic route. These checks still exit 0.

## Runtime migration

The NCUA Ollama index was rebuilt locally from 1,410 source documents:
1,949 fixed chunks and 1,394 semantic chunks. Old MiniLM collections remain
intact. The live API reports ready with Ollama generation and embeddings;
both fixed and semantic API queries retrieved five passages and produced
validated, cited answers with OpenAI credential variables removed. Measured
query times were 8.253 seconds (fixed) and 99.36 seconds (semantic); these are
individual smoke checks, not a latency benchmark. The temporary audit API
stopped when the check completed.

## Publication

Changes are local and have not been committed, pushed, or deployed by this audit.
Private environment files, credentials, dependency installations, build outputs,
and local vector databases are excluded from publication.

Final changed-file checks: 85 Python sources/notebook code cells parse; no
credential-pattern matches or exact matches to known private credentials were
found. `git diff --check` passes. TypeScript incremental-build caches are ignored.
