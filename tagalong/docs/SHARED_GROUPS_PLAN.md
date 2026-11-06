# Shared-workspace Groups: proposed integration

Status: owner approved; implemented on feat/shared-groups, local verification complete; PR review/deployment pending. November 6, 2026. Baseline: `checkpoint/all-projects-2026-11-04`, last verified HEAD `8fb375f`. No production migrations/deployment or paid provider calls are included. The proposal below records the approved design; implementation results follow at the end.

## Evidence and intended experience

**Observed:** The connected Groups page currently returns a demo-mode explanation and mode-switch button rather than group cards. The shared editor and service fix owner identity to Alex. Manual connected creation omits groupId, and the normal connected path uses PlanGenerator. [groups.tsx:12–15](../src/features/planning/groups.tsx:12), [group-editor.tsx:16,31](../src/features/planning/group-editor.tsx:16), [group-service.ts:5,43](../src/services/group-service.ts:5), [create-plan.tsx:28,35,46](../src/features/planning/create-plan.tsx:28), [store.tsx:86–87](../src/features/planning/store.tsx:86).

**Inferred proposal:** Reuse the cards, theme presets/custom theme, suggested/editable unique names, member-row editor, archive/restore/remove controls and Plan with this group action in the signed-in workspace. The owner is the authenticated user (for example ShyamK); there are no fictional starter groups in real accounts. Show an empty-state Create a group action until the owner saves a group. Keep colors, typography and responsive behavior unchanged.

## Small first version and access boundary

**Inferred proposal:** Groups initially belong to their creator: a reusable private roster accessible to that account across devices, loaded from the backend on navigation/refresh. Other people do not gain access to the roster or a plan merely because their alias/email was entered. Collaborative editing, group-level invitations, ownership transfer and realtime group subscriptions are deferred.

**Inferred proposal:** Keep preferred alias required, email and first/last name optional, and adult-only data instructions. Reuse current limits and normalization. Optional contact fields remain owner-visible group data; only minimal aliases and group labels are carried into planning context. Keep contact emails/legal names out of AI prompts, logs and plan data visible to other participants. No local demo data is automatically imported into an account.

**Inferred proposal:** Plan with this group preselects the roster; normal creation can select an existing group, create a new one inline, or proceed without one. Preserve both manual creation and the reviewed generated-draft path. Clearly present the selected roster as intended participants, distinct from authenticated members. Reuse current explicit owner-controlled plan membership/private-link controls to grant access; saving or selecting a group sends no invitation. The final plan review must explain who has access and who still needs an invitation. Do not silently turn local aliases into authenticated voters/chat authors. [existing membership controls](../backend/tagalong/app.py:85), [existing link acceptance](../backend/tagalong/invitations.py:33).

**Inferred scope decision for approval:** This first version provides reusable rosters and shared-plan integration while retaining the current account-based invitation mechanism. The original product target of no-account participant responses remains separate work; this change must not claim to implement it.

## Backend and data plan

**Observed:** Persistence currently serializes a JSON state aggregate in a locked PostgreSQL row; it does not store each new domain entity exclusively in its own table. The aggregate is not directly accessible to anon/authenticated database clients. [repository.py:36–48](../backend/tagalong/repository.py:36), [migration:2–15](../supabase/migrations/202611040001_tagalong.sql:2).

**Inferred proposal:** Extend that existing server-side aggregate with optional groups data using safe defaults for old state, instead of introducing a second persistence mechanism. A group has id, authenticated owner_id, name/theme, adult contacts, archived flag and revision. Internal contact IDs are not auth user IDs. Enforce owner-specific normalized name uniqueness and owner-only access within the existing transaction. Include revision checks to avoid overwriting another device's edits. Record bounded audit metadata without contact content. No SQL migration is expected for this first version because the JSON aggregate already persists extra keys; verify this against repository and coordination behavior before coding. No existing database is modified during development review.

**Inferred proposed API:** Authenticated GET/POST `/v1/groups`, PATCH/DELETE `/v1/groups/{id}`. PATCH covers editing and archive/restore with expected_revision; deletion also checks revision and ownership. Use existing actor/suspension/workspace-mode conventions; reject cross-owner reads/writes. Bind owner identity server-side, never from client-supplied owner_id.

**Inferred proposal:** Add optional group_id and expected_group_revision to manual creation and generated-draft acceptance. Server verifies owner access and active/current group, then snapshots minimal group identity/aliases with the plan. It does not promote contacts to auth membership or send messages. Make snapshot fields immutable through existing general plan update/patch paths. Existing plans without a group and existing invitation/vote/auth models remain valid. A later group edit/archive/removal cannot change an existing plan's membership, votes, chat or snapshot. [strict creation model](../backend/tagalong/models.py:38), [current create route](../backend/tagalong/app.py:76), [generated acceptance route](../backend/tagalong/coordination_routes.py:89).

## Proposed file changes

| Area | Files |
| --- | --- |
| Reusable UI | `src/features/planning/groups.tsx`, `group-editor.tsx`; remove shared-mode gate, pass real owner, mode-aware copy and async save/error handling |
| Both plan paths | `src/features/planning/create-plan.tsx`, `plan-generator.tsx`, `store.tsx`, `src/services/coordination.ts`; group selection/inline editor, preserved drafts and final intended-participant review |
| Contracts/adapters | `src/services/types.ts`, `connected.ts`, `group-service.ts`; retain isolated demo adapter, add authenticated backend operations and owner-parameterized validation/name suggestions |
| Backend domain | New `backend/tagalong/groups.py`; bounded models, access/revision/uniqueness checks and CRUD routes |
| Existing server integration | `backend/tagalong/app.py`, `models.py`, `core.py`, `coordination_models.py`, `coordination_routes.py`; route registration, optional group selection/snapshots, reject snapshot tampering |
| Persistence | `backend/tagalong/repository.py` only if inspection shows support needed beyond aggregate defaults; avoid unrelated schema/repository rewrite |
| Tests | New `backend/tests/test_groups.py`, new `tests/shared-groups.spec.ts`; adapt `tests/groups.spec.ts`, `groups-data.spec.ts`, `shared.spec.ts` only where their intentional demo-only boundary assertions change |
| Documentation | `docs/GROUPS.md`, `docs/CONNECTED_STATUS.md`, README as necessary; replace demo-only claims with precise supported behavior |

## Verification and delivery plan

**Inferred proposed sequence:** After approval, create a feature branch from the checkpoint baseline. Refresh frontend/backend dependencies only with execution approval and frozen lockfiles; establish current baseline. Implement/test domain authorization and persistence first, then adapters and reused UI, then both plan-creation paths. Use synthetic actors and the existing memory/test HTTP fixture, not live provider credentials. The Next.js instructions require reading the relevant installed framework guide before writing frontend code.

**Inferred proposed acceptance tests:**

- Signed-in ShyamK sees their own Groups screen; another account cannot read/edit/delete those groups.
- Save/edit/archive/restore/remove works across independent sessions via the test backend; concurrent stale writes fail clearly.
- Theme/name validation and optional contact fields work; real accounts never receive demo seeds or copied local contacts.
- Group selection works from cards, manual plan creation and generated-draft review; inline group editing preserves the draft; cancelled actions create no plan.
- Plan review labels intended participants separately from authenticated members. Contacts get no read/vote/chat access merely from roster inclusion; existing explicit invitations still work.
- Group contacts are absent from model requests/logs; immutable plan snapshots survive later group edits/removal.
- Existing authentication, plan revisions, chat/votes, administration, discovery, RAG and booking-approval tests remain intact. Group operations require no model calls.
- Desktop/mobile styling and focus remain consistent; connected failures display errors without switching to demo.

**Inferred proposed commands:** `npm run lint`, `npm run typecheck`, `npm run build`, `npm test`, `npm run test:shared`, and backend pytest using the documented locked environment. Provider-backed calls, migrations and production deployment are not authorized by this proposal. A reviewed PR targets `checkpoint/all-projects-2026-11-04`; redeployment follows verified integration with the service owner, not a direct main push.

**Inferred main risks:** Mistaking a contact list for authorization; leaking optional contact details across users or into AI; missing the generated-plan path; stale edits across devices; mixing demo/connected data. The owner-only roster, authenticated server checks, minimal snapshots and explicit invitation boundary address these without introducing group roles or automatic messaging.


## Implementation evidence and local verification

**Observed — implemented:** Backend owner-private groups with bounded contacts, per-owner name uniqueness, revision-protected CRUD and metadata-only audit events live in `backend/tagalong/groups.py`. `models.py` validates paired group/revision input and minimal snapshots; `core.py` resolves owned active groups and forbids snapshot tampering. Generated-draft acceptance uses the same creation checks. Existing aggregate persistence saves these records without new tables or migrations; the fake-cursor repository test verifies the state write and absence of membership/plan projection changes for group-only writes.

**Observed — frontend:** Shared Groups uses the existing cards/editor/themes with the authenticated owner, async backend saves, explicit errors and session-scoped state. Demo storage remains independent. `group-picker.tsx` is reused by manual creation and generated-draft review; inline creation retains form state. `workspace.tsx` distinguishes intended aliases from authenticated members with access. Optional contacts are not copied to plans or sent to generation requests. Existing owner-controlled invitation behavior is unchanged.

**Observed — execution/results (November 6):** Locked npm/uv installs completed without changing dependency manifests/lockfiles. Initial checkpoint lint/typecheck/build passed; baseline backend was 195 passed/1 skipped and shared browser baseline was 24 passed. The initial frontend baseline was 109 passed/1 failed: mobile End-key caret movement was not portable. Its test now undoes the preceding ArrowLeft with ArrowRight, preserving the original behavioral assertion.

Final checks:

- `npm run lint`: passed without warnings.
- `npm run typecheck`: passed.
- `npm run build`: passed with standalone production output.
- `npm test -- --workers=2`: **110 passed (35.8s)**.
- `npm run test:shared`: **32 passed (47.7s)**, including both desktop/mobile Groups cases with the local HTTP fixture, synthetic accounts and fake providers.
- `backend/.venv/bin/python -m pytest tests -q` from backend (equivalent interpreter command `.venv/bin/python ...` there): **201 passed, 1 skipped**. The PostgreSQL integration test is gated on a dedicated test database; no real database/RLS execution or live Supabase verification is claimed.
- `git diff --check`: passed. Signed-in desktop Groups screenshot inspected; browser tests also exercise mobile layout and existing demo visuals. Generated screenshots and test artifacts are ignored and reproducible through the normal tests, with no dependency on root workspace/ files.

**Observed — tested boundaries:** Independent sessions see the same owner's saved groups through the backend fixture; another account receives 404. Stale, archived or unauthorized group selection cannot create a plan. Full snapshots and patches cannot replace/remove group snapshots. Contacts never grant plan access; existing invitations still grant explicit access. Sign-out/account switching ignores delayed group responses. Both manual and AI-reviewed creation keep minimal aliases without optional contact fields. Deleting a group leaves existing plan content intact.

**Observed — rollout boundary:** No production credentials, migrations, paid provider calls, deployment, main/deployment-branch push or automatic messaging occurred. PR base choice is pending owner clarification: current remote CONTRIBUTING.md now says main, while the initially approved plan targeted checkpoint. The checkpoint received a concurrent Discover change after this feature branched; it must be preserved during reviewed integration rather than overwritten. The local feature remains based on 8fb375f until the selected review base is synchronized.
