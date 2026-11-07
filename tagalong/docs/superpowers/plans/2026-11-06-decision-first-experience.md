# Decision-first experience implementation plan

> For agentic workers: use superpowers:subagent-driven-development or superpowers:executing-plans to execute and review each task.

**Goal:** Implement the approved decision-centric homepage and workspace without changing Tagalong's visual identity or publishing.
**Architecture:** Persist versioned decisions/comments/finalization in the existing transactional state; derive consensus from ballots. A typed frontend service and demo adapter feed reusable cards, the default Decisions workspace and responsive momentum panel.
**Tech stack:** Existing Next.js/React/Tailwind, FastAPI, transactional JSON state, pytest and Playwright. No new dependency or production migration.
**Spec:** ../specs/2026-11-06-decision-first-experience.md (owner approved implementation and full testing).

## Constraints
- Preserve coral/graphite/cloud palette, font, shell, roles, invitations, existing tools and legacy tabs.
- Missing replies and objections block confirmation; only owner confirms/finalizes. 100% requires durable finalization; no automatic bookings/messages.
- Existing working details seed proposed options only. Stable member identities; no demo contacts in connected context.
- No publish, push, production data change, real email or paid model calls. Test with synthetic fixtures.
- Reuse isolated integration checkout with installed dependencies; synchronize tested source to unpublished codex branch. Never stage/commit that checkout's old index.

## Tasks
- [x] Backend: failing rule/API tests, versioned CRUD/responses/comments, confirmation/finalization/idempotency, membership/revision invalidation, evidence context and booking guards; targeted tests pass.
- [x] Frontend service/demo adapter: matching contract, persisted isolated demo state, consensus parity fixtures, failures/current-session guards.
- [x] Decision workspace: default Decisions, options/votes/comments/summary/final review, desktop panel/mobile drawer; browser tests fail then pass.
- [x] Homepage: specified composer, action cards, rich consensus plan cards, activity and participation; preserve reviewed generation/manual fallback; tests fail then pass.
- [x] Independent full-change review, fix findings, full lint/typecheck/build/frontend/shared/backend checks and responsive screenshots.
- [x] Update docs and report ready to publish with exact evidence and limitations; do not publish.

## Review focus
- Partial votes, all abstentions, ties and stale summaries never become confirmed consensus.
- Cross-plan IDs, revoked members, foreign ballots and nonowner finalization denied.
- Option, member and plan-outline edits invalidate stale confirmations/finalizations atomically.
- Legacy Chat links/recovery/admin/local Groups remain functional and isolated.
- Long labels, comments, mobile drawer keyboard behavior and interrupted requests preserve usable state.

## Execution ledger
- Owner approved design, implementation and full local test suite; publication explicitly held.
- Existing isolated source checkout: `.repository-backups/tagalong-integration/tagalong`; root branch `codex/decision-first-experience`.

- Implementation complete in isolated checkout. Backend 204 passed/1 gated skip; initial full frontend 121 passed/7 failed, all seven fixed; second frontend132 passed. Final comment-pagination fix has genuine failing old-build regression and independent review approval; final rebuild/rerun pending. Shared first run identified provider health-context contract mismatch and old default-tab selectors; fixes applied, final shared rerun pending.
- Ruling: legacy polls are not silently converted. Strict decision booking gate engages on explicit decision mutations; legacy read-only visits retain previous poll/owner safeguards. No source data or production changes.
- Independent reviewer found and verified fixes for missing structured AI context return, server-owned booking records reopening decisions, actor/role narrative cache and pagination depth reset. No remaining P1/P2 in reviewed source.

- Final shared26passed; backend204passed1skip. Homepage priority tie now uses last activity so a newly created plan appears among equally urgent top3 actions (shared regression confirmed). Final frontend134 rerun on that build passed. Latest lint/typecheck/build passed; 320/390/768/1440 screenshot overflow checks and visual inspection passed; scan43files found no secrets or large artifacts.
- Concurrent teammate commit `3dd344b` / PR3 updates Discover on deployment branch, not mergedmain. It is intentionally separate from this tested local candidate; no push/merge/publication was performed. Reconcile before eventual publication.

- Completion evidence: final standalone build/typecheck/lint passed; frontend134 passed (1.6min); shared26 passed (2.2min); backend204 passed1 gatedskip (60.99s). Reviewed source and staged content scan43files clean; staged whitespace check clean. Screenshots exported to ignored .repository-backups/decision-preview for owner review. No new production changes or paidcalls.
- Public Discover bundle markers confirm teammate PR3 is live from its deployment branch; GitHub PR3 remains open/unmergedmain. This local decision-first branch remains intentionally unpublished and does not include PR3. Preserve and reconcile that separate change before a future deployment.

- November 6 owner explicitly authorized merging PR3 with the redesign, full combined tests, and publication without losing Shyam's changes. Local merge of 3dd344b completed without conflicts; combined verification and release are in progress. Prior publication hold is revoked for this combined release.

- Combined PR3 source verified: lint/typecheck/productionbuild passed; frontend134 passed1.7min, backend204 passed1SQLskip70.16s, shared26 passed2.2min. The first sharedrun exposed skeleton-selector ambiguity; fixed screenshot assertion to actual article results and reran entire26 green. Shyam's four production source files match3dd344b exactly. Production route declaration was regenerated by Next build. Approved publication now proceeding with both histories preserved.
