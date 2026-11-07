# Three-member browser journey

Owner request: test the complete plan creation, invitations, responses, comments and finalization flow and fix discovered issues. Use three isolated browser contexts with synthetic identities against the real local API and transactional memory fixture. No production accounts, private plans, invitation emails or paid model calls.

- [ ] Add a third explicit test identity and shared-only browser scenario. Create through UI, join through private links, edit options and have all members participate through UI.
- [ ] Verify missing replies, objections, member permissions, persisted comments, owner-only confirmation/finalization and reopening after edits.
- [ ] Reproduce issues with failing browser assertions, identify root causes, implement minimal fixes and rerun the journey.
- [ ] Run lint/typecheck/build and complete frontend/shared/backend suites as appropriate; document evidence and exact live-service limits.

Existing app design and decision rules remain unchanged. Preserve Shyam's Discover implementation and use the existing isolated test checkout; keep real credentials out of fixtures and outputs.

Findings: browser test navigation initially filled the previous Account field before Join mounted (test wait corrected). Actual HTTP traces reproduced409 response/comment conflicts after othermember changes. A comment draft also reset during revision polling (genuine browser failure). Added one guarded409 rebase for compatible response/comment commands, retained scoped decision cards during metadata refresh and disabled stale submissions. Deferred-session security test reproduced cross-account draft risk; transport now verifies expectedactor and workspace after getSession and before fetch. Five deterministic regressions pass; three-user desktop UI passed2.1min. Mobile and finalwholeapp verification in progress. Independent reviewer reports no remainingimportant findings after scope guard fix.
