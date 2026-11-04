# Pure RAG workspace implementation plan

> **For agentic workers:** Use superpowers:executing-plans with independent corpus and lab work delegated under superpowers:dispatching-parallel-agents.

**Goal:** Remove active report workflows and demonstrate grounded RAG plus real chunking comparisons.
**Architecture:** Independent rag/service.py and rag/grounding.py own retrieval and cited answers. Corpus generator adds long sources. Chunking lab uses actual indexed chunks. Question-only evaluation owns current metrics; historical report modules remain archived compatibility code.
**Tech Stack:** Python, Pydantic, Chroma, Ollama, Streamlit; optional existing OpenAI adapter.
**Spec:** ../specs/2026-10-25-campaign-pure-rag-design.md (approved by user).

## Constraints

- No active report-generation or historical-comparison UI/CLI.
- Keep original sources and historical measurements; no credential publication.
- Ollama default, optional explicitly selected OpenAI; manual filters remain binding.
- New corpus/algorithm identity invalidates old indexes and scores.
- Current evaluations exclude report-generation cases and disclose coverage.

## Tasks

1. Corpus worker: tests first; add twelve diverse long deterministic sources, development questions, preserve original110 documents/hashes; update corpus tests and regenerate data.
2. Lab worker: tests first; add actual same-source three-strategy chunk inspection and filtered retrieval comparison, span/token/overlap disclosure and stale-result handling.
3. Root: tests first; extract an independent RAG service/grounding, corpus-wide question scope; switch active UI/CLI to question/analyst/lab/evaluation only.
4. Root: question-only evaluator and current-only results page; test corpus/model/chunker matching, missing metrics, and exclusion of report cases. Archive old evaluation semantics rather than relabel old data.
5. Integrate, rebuild Ollama indexes, run actual chunk/query checks and retrieval evaluation, update docs, run full relevant tests and independent review, scan credentials.

## Review focus

Source offsets must point to the actual displayed canonical text; no fabricated highlights.
Shared sources must remain available for corpus-wide questions; a selected campaign remains a hard constraint.
LLM answers require valid citations and source support; no KPI/report assembly on the active path.
Evaluation denominators and development/held-out splits must be visible; no old scores shown as new.
Legacy archival tests may still execute archived code, but the active service must import no report renderer/calculator.

## Execution record

- User approved refactor on October25,2026. Work remains local unless publication requested.
- Corpus complete: schema4,122docs with original110 byte-preserved,12 authored
  learning guides1204–1265tokens and12 clearly labeled development questions.
- ActiveUI/CLI use independent rag/service + grounding; no report renderer or
  KPI-workflow module loaded during an actual local answer/retrieval check.
- ChunkingLab verified actual source spans, bounded tokens, unknown-span handling,
  stale-state behavior and matched filters. Live counts166/550/707; example3/7/22.
- Independent review found and verified fixes for failed-configuration coverage,
  stale source metrics and extraneous citations. Additional regression excludes
  unsupported cases from relevance means; evaluator versionpure-rag-v2.
- Actual Ollama verification generated a cited answer and measured204 rows:
  132held-out and72development, with zero execution errors. Faithfulness is null.
- Automatic approval review rejected reusing the old RAGAS display. Safely retained
  a current-only question-evaluation page; historical report scores stay excluded.
- Final verification:159 tests pass with three existing RAGAS deprecation warnings.
  All48 publishable changed/new files pass credential scans;23Python sources parse;
  git diff --check clean. App running locally on8504 with live ChunkingLab inspected.
  No commit, push or deployment performed.
