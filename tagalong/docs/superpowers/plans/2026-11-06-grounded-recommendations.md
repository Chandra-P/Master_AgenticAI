# Grounded recommendations implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Tagalong's plan-scoped retrieval materially improve researched option assessments while preserving PostgreSQL as the authority for current facts, preferences, votes, and consensus.

**Architecture:** Fix Pinecone chunk/result handling and report current-source indexing freshness. The research endpoint will retrieve group evidence and public options in parallel, ask the connected model for a bounded cited assessment of the identified options, validate citations and source versions, then return stable fit-based ordering. The existing UI will show evidence-linked assessments; deterministic vote and summary paths remain unchanged.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, OpenAI Responses API, Pinecone, PostgreSQL repository, Next.js/React strict TypeScript, Playwright.

**Spec:** `tagalong/docs/superpowers/specs/2026-11-06-grounded-recommendations-design.md`

## Global Constraints

- Pinecone namespaces remain `tagalong:{plan_id}`; never retrieve across plans.
- PostgreSQL/application logic remains authoritative for current structured facts and ballots.
- Do not add dependencies, database migrations, paid providers, external accounts, or production writes.
- Public search data remains unverified and cannot establish venue safety, availability, prices, or bookings.
- Every model claim must cite only verified request evidence; absence or uncertainty cannot yield a positive fit.
- Retrieval and assessments remain read-only, bounded, rate limited, source-version checked, and no-store.

## Review Focus

- Stale, deleted, foreign, or source-ID-collision hits must never reach the model: existing `test_foreign_deleted_and_stale_retrieval_hits_are_not_supplied` plus new research citation allowlist tests.
- A hit on a nonzero chunk must return the complete matching chunk: add regression tests for chunk 1 in assistant and Group Fit.
- Pending or failed current ingestion must be distinguishable from successful, current indexing: add status tests for complete, pending, failed, and empty plans.
- No evidence or retrieval failure must not produce a falsely personalized ranking: add no-evidence and outage research tests.
- Unsupported/model-fabricated citations and over-budget options must not appear supported: add malformed citation and deterministic budget assessment tests.

---

### Task 1: Correct Pinecone retrieval result and chunk handling

**Files:**
- Modify: `tagalong/backend/tagalong/providers.py`
- Modify: `tagalong/backend/tagalong/app.py`
- Modify: `tagalong/backend/tagalong/group_fit.py`
- Test: `tagalong/backend/tests/test_group_fit.py`

**Interfaces:**
- Retrieval candidates retain `id`, `version`, `chunk`, and a bounded numeric `score` when supplied by Pinecone.
- Consumers continue to resolve authoritative source text from Postgres; Pinecone metadata never becomes source text.

- [x] Add failing tests proving Group Fit chunk 1 returns `[6000:12000]` (not a 3000-character prefix), and duplicate Pinecone chunks for one source retain the best-scoring candidate.
- [x] Run the focused tests and confirm the chunk-selection assertions fail on the current implementation.
- [x] Implement best-hit deduplication with bounded score validation in `providers.py`; preserve plan namespace, top-k limits, timeout behavior, and metadata version checks.
- [x] Correct selected chunk slicing and excerpt/truncation metadata in `group_fit.py`; confirm the assistant's existing slice retains the full selected chunk.
- [x] Run focused backend tests and confirm current authorization/source-version tests remain green.

### Task 2: Report current ingestion freshness

**Files:**
- Create or modify: `tagalong/backend/tagalong/retrieval_status.py` (keep the helper isolated if useful)
- Modify: `tagalong/backend/tagalong/group_fit.py`
- Modify: `tagalong/backend/tagalong/research.py`
- Test: `tagalong/backend/tests/test_group_fit.py`
- Test: `tagalong/backend/tests/test_research.py`

**Interfaces:**
- Per-plan status is `{status: 'current'|'pending'|'failed', current_sources, indexed_sources, pending_sources, failed_sources}`.
- Only the latest job whose version matches each active source counts; deleted and older versions do not count as current indexed sources.
- Empty plans report `current` with zero sources.

- [x] Add failing tests for empty, all-current, pending, expired-running, and failed current-version jobs.
- [x] Implement a pure helper over repository state; do not include source text or provider details in the status.
- [x] Include status in Group Fit and research responses, distinguishing successful retrieval from index freshness.
- [x] Add API tests that another plan's ingestion jobs never affect returned counts.

### Task 3: Assess researched options against retrieved group evidence

**Files:**
- Modify: `tagalong/backend/tagalong/providers.py`
- Modify: `tagalong/backend/tagalong/research.py`
- Test: `tagalong/backend/tests/test_research.py`
- Test: `tagalong/backend/tests/test_group_fit.py`
- Test: a focused provider contract test in `tagalong/backend/tests/test_research.py` or `test_group_fit.py`

**Interfaces:**
- Add provider method `assess_research_options(options, evidence, facts) -> list[assessment]` with one bounded structured response for up to eight identified venue options.
- Assessment shape: `{option_id, verdict: 'fits'|'conflicts'|'needs_info', summary, matches: [{text, source_ids}], conflicts: [{text, source_ids}], unknowns: [text]}`.
- Research options include `assessment` when available; top-level response includes an assessment execution status and per-plan indexing status.
- Retrieval query combines the user's search phrase/category with plan location/dates and confirmed preference labels; unconfirmed proposals are not treated as group constraints.
- Assessment execution status is `available` or `unavailable`; each option's assessment is either `{verdict, summary, matches, conflicts, unknowns}` or `null`.
- Index freshness status is `{status: 'current'|'pending'|'failed', current_sources, indexed_sources, pending_sources, failed_sources}`.

- [x] Add failing endpoint tests where a distinctive saved group constraint changes a synthetic option from fit/unknown to conflict and cites the saved source; compare with the same request without that source.
- [x] Add tests ensuring only identified options are assessed, public provenance is included, and private evidence stays within the same plan.
- [x] Add failure tests for no options, no evidence, unavailable retrieval, invalid structured output, fabricated citation IDs, stale evidence, and model outage; search options must remain visible with an explicit unavailable assessment state.
- [x] Implement the strict structured provider call with bounded options/evidence, untrusted-data instructions, no external tool execution, no implicit persistence, and citation-ID enum constrained to evidence supplied.
- [x] In `research.py`, build the retrieval query from the search text, category, location, dates, and confirmed preferences; assess results after concurrent retrieval/search, enforce citations and source versions, enforce deterministic budget conflicts when an estimate exists, and stable-sort by verdict (`fits`, `needs_info`, `conflicts`) while preserving provider order within a verdict.
- [x] Keep retrieval failure and indexing lag separate in the receipt; never label retrieved evidence as unique or complete when the index is behind.
- [x] Run focused backend tests and confirm no plan state changes during research.

### Task 4: Show evidence-grounded rankings on option cards

**Files:**
- Modify: `tagalong/src/services/option-research.ts`
- Modify: `tagalong/src/services/group-fit.ts`
- Modify: `tagalong/src/features/planning/research/research-results.tsx`
- Modify: `tagalong/src/features/planning/group-fit.tsx`
- Modify: `tagalong/src/features/planning/group-fit.css`
- Modify: `tagalong/src/features/planning/research/option-workbench.css`
- Test: `tagalong/tests/shared-research.spec.ts`
- Test: add focused component coverage using the existing frontend test setup if available.

**Interfaces:**
- TypeScript response types mirror the validated API fields exactly.
- Each option card shows assessment status, evidence-backed matches/conflicts, unresolved questions, and expandable source links; unavailable or unassessed output is plainly labeled.
- Research receipt shows retrieval, index freshness, public search, venue identification, and assessment as separate operations.

- [x] Add failing shared UI assertions for fit/conflict labels, cited saved source, index-pending disclosure, and assessment-unavailable fallback.
- [x] Implement accessible source expansion and statuses without changing the existing select/propose workflow or implying consensus.
- [x] Verify the focused flows and full frontend/shared browser suites at desktop and mobile widths.

### Task 5: Document correct RAG boundaries and demo evaluation

**Files:**
- Modify: `tagalong/docs/GROUP_FIT_RAG.md`
- Modify: `tagalong/docs/DEPLOYMENT.md`
- Modify: `tagalong/docs/CONNECTED_STATUS.md`
- Create: `tagalong/docs/evaluations/2026-11-06-retrieval-ablation.md`

- [x] Document which capabilities are RAG, SQL/context-grounded, web search, or deterministic; explicitly state that votes, consensus math, and cross-plan learning are not RAG.
- [x] Document worker/index freshness verification using existing Render configuration and health endpoint; do not claim it is enabled in production without evidence.
- [x] Create a synthetic retrieval ablation scenario and expected evidence/output differences; avoid real user data, paid API calls, and fabricated live claims.
- [x] Run backend tests, frontend lint/typecheck/build and existing frontend/shared suites; record actual outcomes and limitations.
- [x] Review final diff for source isolation, API compatibility, citation validation, and docs consistency.

## Verification recorded 2026-11-06

- Backend: 271 passed, 1 gated SQL skip.
- Frontend: 164 passed, 4 skipped across desktop/mobile.
- Shared authenticated browser suite: 60 passed, 4 skipped across desktop/mobile.
- Lint and TypeScript: passed.
- Webpack production build and standalone packaging: passed. Default Turbopack build failed in the local Windows environment when a CSS processing worker exited without output; rerunning with `next build --webpack` completed successfully.
- Browser/API fixtures use synthetic adapters and in-memory state; no live provider requests, production data mutations, push, or deployment.

