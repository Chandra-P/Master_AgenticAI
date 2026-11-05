# Tagalong connected implementation plan

Spec: ../specs/2026-11-04-connected-design.md

## Task 1: Backend and persistence
- [x] Write failing API/security/workflow tests before implementation.
- [x] Implement FastAPI models, authorization, Supabase repository with versioned transactions, and membership sharing.
- [x] Implement LangGraph, OpenAI structured responses, Pinecone source-scoped retrieval, worker and migration.
- [x] Run backend tests and document results.

## Task 2: Frontend connection
- [x] Add failing connected-mode browser tests for session gate and unavailable service behavior.
- [x] Implement Supabase session UI, asynchronous planning adapter, error/conflict recovery, Realtime invalidation, and account view.
- [x] Connect assistant/proposal confirmation/member sharing and show evidence. Keep demo tests working.
- [x] Run lint, typecheck, build, desktop/mobile tests.

## Task 3: Public release
- [x] Add Docker, Render blueprint, CI, environment examples and setup docs.
- [x] Independently review security and integration contracts, correct findings and rerun affected suites.
- [ ] Configure Supabase and hosting when account access is available; apply migration and configure secrets without logging values.
- [x] Build frontend and backend containers in GitHub Actions; Linux lint, typecheck, build and both browser suites also passed for implementation commit 1dc7646.
- [ ] Run live two-user flows, database RLS checks, hosted startup and public URL smoke.

## Review focus
Unauthorized plan IDs; stale concurrent snapshots; stale vectors after deletion; invalid provider output; session expiry and network failures. Never claim publication from a successful local build alone.

## Progress and rulings
Architecture approved in conversation. Implementation isolated on feat/tagalong-connected in the integration checkout; reviewed source is synchronized to the user's tagalong folder. User work outside Tagalong is untouched by this implementation.

Final review required fail-closed configuration handling and narrow PATCH mutations for growing plans. Both were covered by failing regressions before fixes. Final checks: lint/typecheck/build passed; 60 backend tests passed with one dedicated SQL test skipped; 18 demo/config/update tests and 4 shared browser tests passed. Live OpenAI/Pinecone RAG smoke passed. GitHub Actions also passed both Docker builds and the Linux suite for implementation commit 1dc7646. Supabase/SMTP/hosting verification remains pending external accounts.
