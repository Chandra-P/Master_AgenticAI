# Integrate reusable Groups into the deployed app

**Authorization:** Owner approved integration, conflict resolution, testing and deployment after the branch mismatch was identified. Preserve newer connected functionality; do not switch hosting to the older main snapshot.

**Source:** ShyamK commit `895593a` on main. Merge history into `checkpoint/all-projects-2026-11-04`, resolving conflicts in the isolated integration checkout and synchronizing tested source before committing the merge.

**Scope:** Reusable themed groups, local storage adapter, editor, archive/restore/remove, Groups navigation, demo plan selection and inline group creation. Contacts stay in local group storage; plan snapshots contain aliases/colors only. Groups must be available only in explicitly labeled local demo mode. Connected mode shows an explanation and a demo switch, retains actual authenticated membership/invitations, and never sends group contacts or synthetic participants to the backend or AI.

**Files:** Add group route/editor/page/service/tests; merge additive types, seed data, mock creation, store/context and create dialog changes. Preserve current account/admin/recovery/Chat/RAG/MCP/coordination behavior, existing CSS and dialog callers. Retain the teammate's design/audit documents as historical snapshots with a clear integration note.

## Checks
- [x] Data/store/create integration and contact isolation regressions.
- [x] Navigation/UI/dialog/CSS integration and original group scenarios.
- [x] Connected-mode boundary and no automatic membership/plan mutation tests.
- [x] Independent review, lint, typecheck, build, frontend/shared/backend tests, visual inspection.
- [ ] Resolve all merge paths, scan staged content, commit merge/push and verify public rollout.
