# Tagalong verification and release status

Updated 2026-11-04. The connected application is implemented and locally tested, including the real Supabase database bootstrap and access policies. It has **not been publicly deployed**; production email delivery, full live-account signup and hosting remain unverified.

## Implemented

- Supabase account/sign-in UI and explicit separation of shared and browser-demo workspaces.
- Authenticated FastAPI services, membership checks, revision conflicts and durable Postgres persistence.
- Group chat, one-current-vote-per-member polls, shared documents, explicit preference proposals/confirmation, and owner-controlled membership revocation.
- LangGraph conditional retrieval, OpenAI structured responses/embeddings, plan-isolated Pinecone namespaces, source/version validation, and leased ingestion retries.
- Production Next.js standalone packaging, frontend/API/worker Dockerfiles, Render Blueprint and scoped GitHub Actions checks.

## Verification performed

| Check | Result |
| --- | --- |
| Frontend lint | Passed |
| TypeScript | Passed |
| Production build and standalone asset packaging | Passed |
| Demo/configuration and narrow-update suite | 18 passed, desktop and mobile |
| Shared HTTP/browser suite | 4 passed, desktop and mobile |
| Backend tests | 60 credential-free checks passed; the previously skipped live SQL test also passed during project bootstrap |
| Existing OpenAI account | Live embedding and Responses requests passed |
| Existing Pinecone account | Read-only index configuration check passed |
| Real provider RAG smoke | Synthetic vector ingestion/query, LangGraph retrieval, current-budget grounding and source citation passed; only the created test vectors were removed |
| Render Blueprint | Validated against the current official JSON schema |
| GitHub Actions on Linux | [Passed for implementation commit `1dc7646`](https://github.com/Chandra-P/Master_AgenticAI/actions/runs/41936859555) |
| Frontend and backend Docker builds | Both passed in GitHub Actions |
| Supabase project bootstrap | Database connection verified; seven Tagalong tables created; RLS enabled on all seven |
| Real database/RLS check | Passed on the empty pre-launch project; synthetic auth users, plans and memberships were rolled back |
| Local connected readiness | Frontend and API health checks passed with the actual Supabase project |

Shared browser tests use the real local FastAPI HTTP server with explicit test-only authentication, transactional in-memory persistence and a deterministic assistant. They exercise sharing, denied cross-plan access, documents/citations, chat deduplication, voting, preference confirmation, refresh, membership revocation and delayed-response sign-out isolation. Small shared edits use bounded PATCH operations instead of resending private conversation history; regressions cover histories exceeding the proxy's single-request limit. Configuration-fetch failures stop at an unavailable state rather than loading demo data. These tests do **not** exercise live Supabase Auth, production persistence or Realtime. Provider smoke checks use synthetic content and reused credentials stored only in ignored local environment files. The existing Pinecone index has 768 dimensions; embeddings were explicitly reduced to match, with separate Tagalong plan namespaces.

## Remaining public-release work

1. Provision hosting. The Supabase project is now connected and its schema is installed; bootstrap persistence/RLS checks passed before application data existed.
2. Configure production email delivery, confirmation URLs and external-account signup. Verify two real accounts and Realtime invalidations through the deployed app. The rollback-only database/RLS test has passed, but it does not prove email delivery or the full production signup flow.
3. Verify hosted container startup and readiness after provisioning. Both Docker builds passed in GitHub Actions; local Docker remains unavailable in this workspace.
4. Deploy the reviewed branch's frontend, API and ingestion worker; configure server secrets and spend controls; verify the public HTTPS URL and real flows on desktop/mobile.

The dedicated SQL/RLS test is skipped in credential-free CI without `TAGALONG_TEST_DATABASE_URL`; see `backend/TESTING.md`. It was separately run successfully against the selected empty Tagalong project during bootstrap, with all synthetic rows rolled back. Local test adapters are never imported by the production entrypoint. Calendar writes, bookings and live venue search remain disabled. Shared discovery never presents synthetic demo venues as live inventory. The current serialized state aggregate is intended for a small initial rollout; load testing and row-level transaction work are required before large-scale use.

The local ingestion worker has not been started. Automatic approval review requires explicit approval before it continuously sends shared source text to OpenAI for embeddings and stores derived vectors in Pinecone. Existing provider verification used synthetic content only. All connection credentials are stored in ignored local environment files.

See [deployment instructions](DEPLOYMENT.md). No public-release or production-readiness claim follows from this document.
