# Three-member browser journey

Owner request: test the complete plan creation, invitations, responses, comments and finalization flow and fix discovered issues. Use three isolated browser contexts with synthetic identities against the real local API and transactional memory fixture. No production accounts, private plans, invitation emails or paid model calls.

- [x] Add a third explicit test identity and shared-only browser scenario. Create through UI, join through private links, edit options and have all members participate through UI.
- [x] Verify missing replies, objections, member permissions, persisted comments, owner-only confirmation/finalization and reopening after edits.
- [x] Reproduce issues with failing browser assertions, identify root causes, implement minimal fixes and rerun the journey.
- [x] Run lint/typecheck/build and complete frontend/shared/backend suites as appropriate; document evidence and exact live-service limits.

Existing app design and decision rules remain unchanged. Preserve Shyam's Discover implementation and use the existing isolated test checkout; keep real credentials out of fixtures and outputs.

Findings: browser test navigation initially filled the previous Account field before Join mounted (test wait corrected). HTTP traces reproduced 409 response/comment conflicts after other-member changes. A comment draft also reset during revision polling. Added one guarded rebase for compatible response/comment commands, retained scoped decision cards during metadata refresh and disabled stale submissions. A deferred-session security test reproduced cross-account draft risk; transport now verifies the expected actor and workspace after getSession and before fetch. Five deterministic regressions pass. Independent review found no remaining important issues after the scope guard fix.

Integrated Shyam's shared Groups PR4 without overwriting its history. The combined build exposed incomplete group creation wiring; fixed missing callback/type fields, retained selected groups through modal and Home manual fallbacks, and added the intended roster display. The Home regression failed against the previous build and passes against the corrected build. Both roster failures passed after the display correction. See MEMBER_JOURNEY_TESTING.md for exact results, scope and limits.
