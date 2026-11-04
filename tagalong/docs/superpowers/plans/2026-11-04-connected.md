# Tagalong connected implementation plan

Spec: ../specs/2026-11-04-connected-design.md

## Task 1: Backend and persistence
- [ ] Write failing API/security/workflow tests before implementation.
- [ ] Implement FastAPI models, authorization, Supabase repository with versioned transactions, and membership sharing.
- [ ] Implement LangGraph, OpenAI structured responses, Pinecone source-scoped retrieval, worker and migration.
- [ ] Run backend tests and document results.

## Task 2: Frontend connection
- [ ] Add failing connected-mode browser tests for session gate and unavailable service behavior.
- [ ] Implement Supabase session UI, asynchronous planning adapter, error/conflict recovery, Realtime invalidation, and account view.
- [ ] Connect assistant/proposal confirmation/member sharing and show evidence. Keep demo tests working.
- [ ] Run lint, typecheck, build, desktop/mobile tests.

## Task 3: Public release
- [ ] Add Docker, Render blueprint, CI, environment examples and setup docs.
- [ ] Independently review security and integration contracts, correct findings and rerun affected suites.
- [ ] Configure Supabase and hosting when account access is available; apply migration and configure secrets without logging values.
- [ ] Run live two-user flows, provider checks, public URL smoke and report exact results. If external access is missing, finish all independent work and identify the remaining provisioning step.

## Review focus
Unauthorized plan IDs; stale concurrent snapshots; stale vectors after deletion; invalid provider output; session expiry and network failures. Never claim publication from a successful local build alone.

## Progress
Architecture approved in conversation. Implementation isolated on feat/tagalong-connected in integration checkout; final reviewed source will be copied to the user's tagalong folder. Existing user work outside Tagalong is untouched.
