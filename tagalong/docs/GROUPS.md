# Reusable Groups

## Signed-in workspace

**Implemented on `feat/shared-groups`; production rollout is pending review and deployment.** Open **Groups** in navigation to manage reusable rosters owned by your signed-in account. The page reuses the demo's cards, palette, typography, editor and theme presets. Real accounts start without fictional groups.

Create a group with a preset or custom theme and a suggested editable name. Names must be unique within your account, including archived groups. Your signed-in identity is the owner; each additional adult needs a distinct preferred alias. Email and first/last name are optional and private to the owner. Do not enter children's names/photos. Groups save through the authenticated backend and load on navigation/refresh across devices. **Refresh saved groups** reloads the list during plan creation. Group-level collaborative editing and realtime group subscriptions are not included.

**Plan with this group** preselects the roster. You can also choose/create a group during manual plan creation or AI-draft review. Inline group creation preserves the plan draft. A saved group remains even if you cancel plan creation. The final review distinguishes the intended roster from actual authenticated members: a newly created plan initially grants access only to you. Invite people explicitly through the existing **Add member** or private join-link controls. Saving or selecting a contact never sends a message or grants access.

A plan keeps an immutable snapshot of the group name/theme and aliases. Contact IDs, emails and legal-name fields are not copied into the plan or assistant inputs. Later edits, archive/restore or removal of the reusable group leave existing plans, membership, chat and votes unchanged. Archived groups cannot be selected for a new plan. Removing a group removes its private contacts from that account's group list; minimal aliases already captured in existing plans remain part of those plans.

## Storage and access

Owner-private group records are persisted inside the existing transactional PostgreSQL JSON state aggregate (`tagalong_state`), accessed only through authenticated FastAPI endpoints. Owner identity is assigned server-side. Every read/write checks owner access; revisions reject stale edits, including a stale roster selected for a new plan. Existing state without a groups key remains valid, so this change needs no SQL migration or additional credentials.

API: GET/POST `/v1/groups`, GET/PATCH/DELETE `/v1/groups/{id}`. Updates/deletions require `expected_revision`; manual creation and generated-draft acceptance accept paired `group_id` and `expected_group_revision`. Group audit metadata contains actor/group IDs, action and timestamp, without contact fields. Existing database clients remain unable to read the private state aggregate directly.

Account changes/sign-out clear group state and ignore late responses. A backend failure shows an error instead of silently substituting local demo data. Group operations make no AI calls. There is a limit of 100 saved groups per owner and 12 additional adults per group. No age-detection mechanism is claimed: follow the adult-only instructions and use synthetic data for testing.

## Local demo

The demo stays separate, with fictional Alex and browser-local `tagalong-groups-v1` data. It retains the theme/member/editor/archive/removal flow, synthetic seeds and local plan snapshots. It neither imports into an account automatically nor affects shared plans. To explore it, switch explicitly through **Account → Explore the demo**. Connected groups do not load demo contacts.

## Team contribution and rollout

Deployment baseline: `checkpoint/all-projects-2026-11-04`. The previous `895593a` implementation and `16932ce` integration provided demo-only groups; the new shared implementation is on `feat/shared-groups`. Submit a reviewed PR targeting the checkpoint branch, preserve its newer connected features, then coordinate frontend/API deployment with the service owner. Pushing only to main does not update that service. See [CONTRIBUTING.md](../CONTRIBUTING.md) and [approved plan](SHARED_GROUPS_PLAN.md).

Use the normal locked install and documented frontend/backend test commands. No application/test/deployment requires files inside the root workspace/ directory. Local fixtures simulate auth and providers; their passing results do not establish real Supabase or production database verification.
