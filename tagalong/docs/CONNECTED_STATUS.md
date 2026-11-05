# Tagalong verification and release status

Updated 2026-11-04. The frontend and API are publicly hosted on Render. Public readiness and signed-out desktop/mobile checks passed; the user reports receiving confirmation email and successfully signing in. Private join links, preferred display names, and optional embedded indexing are implemented locally; deployment of these latest changes still needs verification. Unrestricted public email delivery and two-real-account collaboration remain unverified.

Frontend: https://tagalong-web-clbe.onrender.com · API: https://tagalong-api-7pdn.onrender.com

## Implemented

- Supabase account/sign-in UI and explicit separation of shared and browser-demo workspaces.
- Authenticated FastAPI services, membership checks, revision conflicts and durable Postgres persistence.
- Group chat, one-current-vote-per-member polls, shared documents, explicit preference proposals/confirmation, and owner-controlled membership revocation.
- Owner-created private seven-day invitation links with replacement/disabling and explicit authenticated acceptance. Preferred names are requested during signup/join and editable on the account page; permissions retain stable account identity.
- Optional embedded ingestion worker for the free Render API pilot; jobs pause while the service sleeps.
- LangGraph conditional retrieval, OpenAI structured responses/embeddings, plan-isolated Pinecone namespaces, source/version validation, and leased ingestion retries.
- Production Next.js standalone packaging, frontend/API/worker Dockerfiles, Render Blueprint and scoped GitHub Actions checks.

## Verification performed

| Check | Result |
| --- | --- |
| Frontend lint | Passed |
| TypeScript | Passed |
| Production build and standalone asset packaging | Passed |
| Demo/configuration and narrow-update suite | 24 passed, desktop and mobile, including signup names and relevant demo-assistant responses |
| Shared HTTP/browser suite | 6 passed, desktop and mobile, including signed-out invitation return and explicit joining |
| Backend tests | 73 passed; one live SQL test skipped without explicit test database configuration |
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

1. Deploy the latest reviewed branch to both existing Render services. Verify the private join link and preferred-name flow using two real accounts.
2. Confirm production email delivery to external addresses and Realtime invalidations. The user's successful signup is evidence for that account, not unrestricted delivery.
3. Enable `TAGALONG_EMBEDDED_WORKER=true` on the existing API service and confirm its health metadata. Free services pause indexing during sleep.
4. Verify new CI/container checks for the latest commit and hosted document indexing with approved data.

The dedicated SQL/RLS test is skipped in credential-free CI without `TAGALONG_TEST_DATABASE_URL`; see `backend/TESTING.md`. It was separately run successfully against the selected empty Tagalong project during bootstrap, with all synthetic rows rolled back. Local test adapters are never imported by the production entrypoint. Calendar writes, bookings and live venue search remain disabled. Shared discovery never presents synthetic demo venues as live inventory. The current serialized state aggregate is intended for a small initial rollout; load testing and row-level transaction work are required before large-scale use.

The user explicitly approved background indexing of shared messages/documents to OpenAI embeddings and Pinecone vectors on 2026-11-04. The local ingestion worker was started with that approval; hosted worker status remains to be verified. All connection credentials remain in ignored local environment files or hosting secrets.

See [deployment instructions](DEPLOYMENT.md). No public-release or production-readiness claim follows from this document.

## Pending requested work

The user requested a separate app-admin role that can coexist with plan ownership or membership, plus multiple persisted QA plans for admin review. These have been discussed but are not implemented or provisioned in this checkpoint. No QA accounts or review plans were created. The existing signed-in account remains the only confirmed application account in the last read-only check.
