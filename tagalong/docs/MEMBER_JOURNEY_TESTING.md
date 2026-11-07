# Multi-user journey verification

The automated journey uses three isolated browser sessions (Alice, Bob and Carol), the real local FastAPI routes and a transactional in-memory repository. Authentication is an explicit test fixture. It does not create production users or plans, send emails, make bookings or call paid AI providers.

## Covered journey

- The owner creates a plan through the UI and creates a private invitation link.
- Two signed-out people open the link, authenticate, choose display names and explicitly join. Private plan details are hidden before authentication.
- The owner proposes options for place, date, budget and activity. All three members respond through the UI.
- Missing responses and objections prevent confirmation. Abstention counts as participation without pretending agreement.
- A member drafts a contextual comment while another member responds. The draft survives refresh, and the posted comment remains visible after reload in a different session.
- A member cannot finalize. The owner confirms decisions and explicitly reviews the final plan. Consensus reaches 100% only after finalization.
- Reopening a decision removes finalized status across all three sessions.
- The complete journey runs on desktop and mobile.

## Fixes identified

Concurrent response/comment saves previously failed on plan-revision conflicts. Only a definite HTTP 409 can now trigger one retry, after checking that decision options, membership and the actor's own ballot remain compatible. Owner actions and uncertain network writes never retry automatically.

Decision cards now retain their identity and drafts while plan metadata catches up. Stale controls are temporarily disabled. Account and workspace identity are rechecked after asynchronous session acquisition and immediately before each request, preventing a previous user's draft from being submitted using a new user's session.

The combined shared Groups update also needed its plan-creation wiring completed: typed group revision checks, selected group retention through manual creation, and group selection in AI draft review. Contact details remain excluded from the AI generation request and the plan roster.

## Run locally

From the Tagalong directory, with dependencies and the backend virtual environment prepared:

```text
npm run lint
npm run typecheck
npm run build
npm test -- --workers=2
npm run test:shared
```

Run the backend pytest suite using the project's virtual environment. See DEPLOYMENT.md for the existing environment setup. Browser journey screenshots are written to the Playwright shared-test output directory.

## Limits

These tests verify browser behavior, API validation and permissions against the local fixture. They do not verify real Supabase email delivery, production PostgreSQL behavior, provider availability or paid AI quality. Public deployment health checks are separate from authenticated end-to-end testing.

## Results — 6 November 2026

- Backend: 210 passed, one dedicated live SQL/RLS test skipped because no disposable test database was supplied.
- Frontend: 144 passed across desktop and mobile. After the Home group-selection correction, all 36 affected Home, Groups and authentication cases also passed.
- Shared workspace: 36 of 38 passed in the combined run. The two failures reproduced the missing intended-roster display; after fixing it and rebuilding, both complete affected desktop/mobile scenarios passed, including group archival/removal and access-isolation checks. No unresolved failures remain from this run.
- Three-member UI journey: passed on desktop (2.1 minutes) and mobile (2.2 minutes) in the combined run.
- Final production build, lint and explicit TypeScript check: passed.
- Independent review identified the asynchronous account-switch race and Home group fallback; both were fixed and regression-tested. No remaining important findings were reported for those corrections.

The teammate Discover and shared Groups histories are retained in the combined branch. No production account, plan or booking was changed for these tests.
