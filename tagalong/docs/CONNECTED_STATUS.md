# Tagalong verification and release status

## Reusable Groups integration — 2026-11-06

ShyamK's `895593a` Groups commit is integrated into the current deployment branch while preserving authenticated planning, admin access, RAG and MCP booking demos. Groups are explicitly browser-local demo data; connected users see an explanation and can choose **Explore demo groups**. They do not create shared memberships or send invitations. See [Groups](GROUPS.md).

Verification: lint, TypeScript, production build and 110 desktop/mobile frontend tests passed; backend tests passed (195, with one gated SQL skip). Desktop/mobile Groups visuals were inspected. All 24 shared-workspace tests passed, including contact isolation and unchanged membership checks. Public Groups rollout was verified for merge `16932ce`: `/groups` returned HTTP 200 and its published bundles contained the connected-mode explanation and demo Groups UI. GitHub CI was still running at that check; local checks above are complete. The earlier release records below retain their historical scope.

Updated 2026-11-06. This release hardens mobile typing acceptance and transient shared-service reads, and includes a 1080p male/female narrated competition demo with a qualified four-case live evaluation. It retains **Group fit**, a read-only RAG assessment with verified sources, explicit uncertainty and deterministic budget conflicts. Lint, typecheck, production build, 195 backend tests (one gated SQL skip), 90 frontend tests, and 22 shared-workspace tests passed. A live synthetic smoke check completed a Pinecone query against a fresh empty namespace and produced a valid cited OpenAI assessment from supplied test evidence; no private plans or index writes were used. The shared suite verifies authenticated flow and unchanged plan state using synthetic retrieval/model adapters. Public rollout remains a separate check from these local results.

Frontend: https://tagalong-web-clbe.onrender.com · API: https://tagalong-api-7pdn.onrender.com

Current feature and configuration guides: [Group fit RAG](GROUP_FIT_RAG.md), [typing behavior](DISCOVERY_NOTES_TYPING.md), [deployment](DEPLOYMENT.md), and [contributor code map](../CONTRIBUTING.md). This release's public rollout is pending verification. Earlier checkpoint notes below preserve their original test/deployment limits; statements that a historical change still required deployment describe that checkpoint, not the current hosted version.

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
| Demo/configuration and narrow-update suite | 32 passed, desktop/mobile, including suspension clearing and the role-switch/sign-out race |
| Shared HTTP/browser suite | 16 passed, desktop/mobile, including all three replays, Admin/Member switching, direct-link QA isolation and existing collaboration flows |
| Backend tests | 97 passed; one live SQL test skipped without explicit test database configuration |
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

The dedicated SQL/RLS test is skipped in credential-free CI without `TAGALONG_TEST_DATABASE_URL`; see `backend/TESTING.md`. It was separately run successfully against the selected empty Tagalong project during bootstrap, with all synthetic rows rolled back. Local test adapters are never imported by the production entrypoint. Calendar writes and bookings remain disabled. Connected Discover now supports authenticated Keenable web search with external source links; snippets are not verified venue inventory. Shared discovery never presents synthetic demo venues as live inventory. The current serialized state aggregate is intended for a small initial rollout; load testing and row-level transaction work are required before large-scale use.

The user explicitly approved background indexing of shared messages/documents to OpenAI embeddings and Pinecone vectors on 2026-11-04. The local ingestion worker was started with that approval; hosted worker status remains to be verified. All connection credentials remain in ignored local environment files or hosting secrets.

See [deployment instructions](DEPLOYMENT.md). No public-release or production-readiness claim follows from this document.

## App administration and stored QA review

App administration is implemented with server-owned grants, independent plan membership, reason-required audited private inspection, and account suspension/restoration. The existing confirmed user was explicitly granted admin access. Three synthetic QA plans and real OpenAI/Pinecone responses are saved for that user; all three live budget/citation/isolation checks passed. No new auth accounts or real invitations were created. See [saved review plans and verification limits](QA_REVIEW.md). Deployment of this latest admin code is still required before the public `/admin` dashboard can be used.

Sign-in now explicitly asks **Member** or **Admin**. Admin mode requires an existing server grant; Member mode hides QA plans and denies their direct URLs. The dashboard, navigation and storyboard APIs require Admin mode. Mode choice is tab-scoped, tied to the account, and cleared on sign-out. Role changes invalidate pending private responses.

Three admin-only fictional storyboards illustrate Christmas in San Francisco, a four-person three-day Yosemite trip and a San Francisco date night. They have step-by-step replay and evolving plan snapshots, and do not create real user accounts or member plans. Their scripted AI illustrations are explicitly labeled. See the [presentation narrative](DEMO_PRESENTATION.md).

Owner controls now support confirmed transfer to an existing active member and confirmed access deletion for all plan members. Deleted records are retained and marked for audited admin review; source/vector removal is queued. No existing live user plan was deleted or transferred for testing.

The proactive coordination demo is implemented: natural-language reviewed drafts; the redesigned homepage; stored summaries, explicit decisions and open questions; derived health and stalled detection; next actions; preference-grounded activity ideas; four-node LangGraph dispatch. Live synthetic OpenAI checks passed. The additive coordination projection migration is applied. Local checks passed and independent review found no remaining important issues; deployment of this latest update must still be checked. See [architecture, endpoints and rollout](PROACTIVE_COORDINATION.md).

The real Postgres coordination projection was additionally tested with a synthetic plan inside a transaction that was fully rolled back. No auth account was created and no plan content persisted from that test. Desktop/mobile visual checks reported no horizontal overflow or page errors.
