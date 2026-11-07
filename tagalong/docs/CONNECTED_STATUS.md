# Tagalong verification and release status

## Grounded option research and retrieval reliability — 2026-11-06

Option research now compares identified public places with plan-scoped evidence before returning results, shows cited matches/conflicts/questions and evidence origin, and reports per-plan indexing freshness. Group Fit preserves source origin and full selected Pinecone chunks. Every research finding must independently cite its own public listing plus the relevant saved group evidence or authoritative fact. Pinecone remains scoped to unstructured plan memory; Postgres remains the source of truth for current facts and votes. The [RAG guide](GROUP_FIT_RAG.md) includes an honest per-feature classification and the [synthetic ablation](evaluations/2026-11-06-retrieval-ablation.md) documents what it demonstrates and cannot prove.

Verification on the isolated integration checkout: backend **271 passed, 1 gated SQL skip**; frontend desktop/mobile **164 passed, 4 skipped**; shared authenticated desktop/mobile **60 passed, 4 skipped**; lint and TypeScript passed. A production Webpack build and standalone packaging passed. Default `npm run build` hit a local Windows Turbopack child-process failure while processing CSS (the worker exited without an error message); this was isolated to the Turbopack build path, and the explicit Webpack build succeeded. The backend/browser suites use synthetic adapters and in-memory persistence; the SQL test is separately gated. No live provider calls, production data changes, push, or deployment were performed for this update.

## Combined PR #3 and decision-first release — 2026-11-06

The owner authorized integration, full combined tests and publication. Shyam's original `3dd344b` Discover commit is merged with redesign `7a75367`, retaining both histories. His four production Discover source files match PR #3 exactly; the existing screenshot test now waits for real restaurant articles rather than matching the new loading skeletons. Next.js regenerated its production route declarations during the build.

Combined lint, TypeScript and production build passed; all 134 frontend tests and 204 backend tests passed (one gated SQL skip). All 26 shared-workspace tests passed on the combined source. Source merge `3ddf663` was published to main and the Render deployment branch. Public checks verified both decision-first homepage and Shyam's Discover controls; API decision, summary and finalization routes; connected web health (200); and unauthenticated decision access denied (401). GitHub marks PR #3 merged. Additional GitHub CI jobs were still running at this check. No migration or new dependency is needed. Earlier release-candidate notes below describe their historical state before this approved integration.

## Decision-first release candidate — 2026-11-06

Implemented the approved homepage and decision workflow on local branch `codex/decision-first-experience`. **Unpublished: no push or deployment has been performed for this release.** The design retains the existing palette/type/shell, adds next-action cards and consensus history, defaults plans to Decisions, persists contextual comments and versioned ballots, supports owner confirmation/finalization/reopening, and exposes bounded evidence-backed decision summaries on explicit request. See [Decision workflow](DECISION_WORKFLOW.md) for state, compatibility rules and release order.

Fresh local checks: lint, TypeScript and production standalone build passed; 134 frontend tests passed across desktop/mobile; 204 backend tests passed with one gated SQL test skipped. All 26 shared-workspace release-candidate tests passed, including two-member consent/comments, durable finalization/reopening and explicit fake-provider AI decision summaries. Responsive screenshots at 320/390/768/1440px passed overflow checks and were visually inspected. Tests use synthetic members, transactional memory persistence and fake providers; these results do not establish live Supabase email, real Postgres/RLS or current production-provider behavior.

Independent review findings were fixed and covered by regression tests: returned AI context, finalization retained across protected booking/cancellation records, actor/role-scoped narratives, malformed transport fallback and older comment-page retention. Existing legacy polls are preserved as unclassified decisions rather than converted to approvals; their booking workflow remains compatible until explicit decision mutations engage the new gate. No schema migration, dependency installation or paid provider call was used. Shyam's Discover refresh from PR #3 (`6549d51`) is present in the current `main` history and is preserved by this release.

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
