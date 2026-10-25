# Campaign metadata and analyst view implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Add validated combined filters, automatic classification, and visible retrieval evidence.
**Architecture:** Shared filter contract feeds both Chroma and BM25. Explicit provider selection defaults to Ollama; server-only OpenAI is optional. Streamlit forms share the same analysis service.
**Tech Stack:** Python, Pydantic, LangChain, Chroma, Streamlit, httpx.
**Spec:** ../specs/2026-10-24-campaign-metadata-analyst-design.md

## Constraints and review focus

- No credential widgets or committed keys. No implicit provider fallback.
- Manual scope intersects inferred scope; conflicts never broaden retrieval.
- AND across fields, OR within fields; validate values against the manifest.
- Dense and lexical candidate pools must obey identical predicates.
- Stale evidence must disappear after inputs/settings/corpus change.

## Tasks

1. Write failing filter tests; implement retrieval/filters.py and Chroma predicate translation. Verify real store and BM25 scoping.
2. Write failing provider/classification tests; implement retrieval/classification.py and optional OpenAI generation adapter; extend server secret whitelist. Verify validation, default local routing, refusals, and redacted errors.
3. Write failing service tests; integrate analysis and optional filters into CampaignService without changing existing report paths. Verify manual scope, empty results, and provenance.
4. Write failing Streamlit interaction tests; add Analyst View and Ask Questions filter disclosure with stale-result protection.
5. Run full regressions, real Ollama smoke, independent code review, source and secret scans; update README. Leave changes uncommitted unless requested.

## Execution record

- Approved by user with OpenAI optional, Ollama default. Implement inline.
- Implemented shared filter contract, provider selection and secret whitelist,
  analysis service, Analyst View, and scoped Ask Questions.
- Ruling: use cheap widget reruns with an explicit action button rather than a
  form; an interaction regression proved forms could retain stale evidence after
  edits. Inference still runs only on submission.
- Review caught bypassed question routing/focusing; fixed using shared
  question_plan and disclosed routing_filters, with red/green regressions.
- Actual local Llama overfilled unspecified metadata even with examples. Added
  constrained candidate labels/aliases, a smaller list-of-constraints schema,
  source-text validation, and a no-constraint fast path. Live specific/general
  questions and scoped dense/hybrid retrieval now pass.
- Final review also caught region prefixes inside campaign IDs; masked ID spans
  before matching other fields and verified an explicit Texas mention still works.
- Final verification: 139 tests passed, three existing RAGAS deprecation warnings;
  live Ollama classification and both retrieval modes passed; 490-chunk local
  section index prepared. OpenAI success/refusal/truncation/error behavior tested
  with mocked HTTP responses; no live OpenAI call was made.
- Source/credential scan: 21 changed/new files, 17 Python files parsed, no API-key
  pattern or known private credential matches; git diff --check clean. Independent
  review confirmed both findings resolved. Changes remain local and uncommitted.
