# Reusable groups: small demo plan

> Historical snapshot from the Groups contribution on main (`895593a`). It describes the older prototype and its original verification. The current connected app and integration checks are documented in [Tagalong release status](../tagalong/docs/CONNECTED_STATUS.md) and [Groups integration plan](../tagalong/docs/superpowers/plans/2026-11-06-groups-integration.md).

## Confirmed context and scope

**Observed:** On November 6, 2026, read-only `lsof` inspection identified a listener on localhost:3000 (PID 69823) whose working directory is this repository's `tagalong/`. This confirms the local server directory, not a completed browser walkthrough. Source still uses browser localStorage and deterministic assistant replies. [mock service](../tagalong/src/services/mock-planning-service.ts:6), [store](../tagalong/src/features/planning/store.tsx:8).

**Owner-approved scope:** Reusable friend/family groups; keep the demo simple. Include group name, adult members/aliases, owner, archive/remove controls, and themes such as Sunday supper, Weekend friends and Family outings. Invitations remain explicit human actions; children can only be represented through aggregate needs, never names or photos. These approvals come from the current conversation, not an existing implementation.

## Approved development plan

**Owner-approved refinement:** The group editor includes theme presets plus manual custom theme, a suggested editable unique group name, preferred name/alias and optional email per adult member, with optional first/last name under More details. Alex creates/owns the demo group. After pre-flight review the owner approved this plan and required matching existing colors, font and visual styling. The following proposal records the approved scope; implementation evidence is at the end.

**Observed pre-flight:** The provider owns all plan state and saves full arrays after readiness; several CreatePlan entry points use the same component. Existing avatars/chat/invite checks expect Member `{name,color}`, and polls cast votes as Alex. No reusable group entity currently exists. The shared Radix dialog wraps child content and the plan dialog contains a form. Mobile navigation has fixed horizontal padding per item, which needs adjustment when adding Groups. [store:8](../tagalong/src/features/planning/store.tsx:8), [create:9](../tagalong/src/features/planning/create-plan.tsx:9), [shell:10](../tagalong/src/components/shell.tsx:10), [avatars:5](../tagalong/src/features/planning/shared.tsx:5), [workspace:17–18](../tagalong/src/features/planning/workspace.tsx:17), [polls:8](../tagalong/src/features/planning/polls.tsx:8), [dialog:5](../tagalong/src/components/ui/dialog.tsx:5), [mobile CSS:9](../tagalong/src/app/globals.css:9).

**Observed baseline limits:** Dependencies and a running local server now exist. Local owner changes include package.json/package-lock.json, tsconfig.json and generated next-env.d.ts; preserve them. Reading installed metadata confirms Next 16.4.5 and eslint-config-next 15.5.29, matching the current manifest. **Inferred:** this mismatch merits a baseline check, but is not a proven failure. Prior build and browser failures remain historical, not current results. No lint/typecheck/build/test or browser walkthrough was executed in this pre-flight. [manifest](../tagalong/package.json:24), [ESLint dependency](../tagalong/package.json:36), [historical results](../tagalong/VERIFICATION.md:5).

**Inferred proposal:** Add a Groups navigation item and `/groups` page. Show synthetic starter groups for Sunday supper, Weekend friends and Family outings. Reuse the application's cards, avatars, buttons and Radix dialog. Themes supply labels and visual accents only, without recurring schedules, generated agendas or AI recommendations. The demo owner is Alex, matching the current fixed persona in [shell](../tagalong/src/components/shell.tsx:10).

| Proposed editor field | Rule |
| --- | --- |
| Theme | Preset Sunday supper, Weekend friends, Family outings; Custom reveals a required trimmed text field (max 60 characters) |
| Group name | Required, editable, max 80 characters; suggest theme + Alex's circle, adding a numeric suffix if needed. Stop replacing it after manual edits |
| Owner | Fixed Alex; automatically included exactly once and cannot be removed in this demo |
| Adult member rows | Preferred name/alias required (max 40); optional email; optional first/last names (max 40 each) in More details; add/remove rows |
| Save/cancel | Validate before saving; cancellation discards editor changes |

**Inferred proposed validation:** Unique trimmed group names ignoring case and repeated whitespace within Alex's browser workspace, including archived groups to avoid restore collisions. Distinct internal UUIDs identify groups/members; names are display labels, not identity keys. Duplicate member aliases ignoring case are rejected because the current plan display is name-based; optional duplicate emails are rejected case-insensitively and nonempty emails must be syntactically valid. Reserve Alex's alias. Limit to 12 additional adults to match current creation behavior; no silent truncation. Owner-only groups are permitted. Explain adult-only data and no invitations sent. These rules cannot automatically determine whether a typed name belongs to a child. [existing member handling](../tagalong/src/services/mock-planning-service.ts:8).

**Inferred proposal:** Each group card offers Plan with this group, Edit, Archive/Restore and Remove. Confirm removal within the UI; removal affects only the reusable group. Archived groups remain manageable but disappear from new-plan choices. Creating a plan offers an existing group, an inline create-group dialog, or the existing one-off participant input. Copy selected aliases into the plan; group edits/removal never rewrite past plan participants or votes. No outbound invitation action is added to this demo.

**Inferred UI integration detail:** “Create new group” within plan creation switches the content of the existing dialog to the shared group editor, then returns to the intact plan draft with the new group selected. Do not nest forms or stack focus-trapping dialogs. Cancelling group creation returns to the draft without adding a group. Saving the group creates a reusable group even if the owner later cancels plan creation. “Plan with this group” opens the same CreatePlan component with that group selected. Keep existing one-off fields, labels and defaults as the default path for regression compatibility. Disable group-changing actions until group storage is loaded; revalidate selected-group existence/archive state on submit. [shared create dialog](../tagalong/src/features/planning/create-plan.tsx:9).

**Inferred proposed data shape:** Add Group `{id, name, theme, ownerId, members, archived}` and separate GroupMember `{id, preferredName, firstName?, lastName?, email?, color}`. Keep existing Member `{name,color}` unchanged. Extend CreatePlanInput with optional groupId and Plan with optional group snapshot `{id,name,theme}`; at creation resolve a current active group and explicitly map only preferredName/color into cloned Plan members. No email or legal-name details enter plans, chat, assistant inputs or avatars. Snapshot metadata never depends on a group still existing. Store groups under a new `tagalong-groups-v1` key, leaving `tagalong-demo-v1` compatible. No SQL migration, backend, API or package additions. [current structures](../tagalong/src/services/types.ts:3), [storage](../tagalong/src/services/mock-planning-service.ts:3).

**Inferred proposed storage safeguards:** Separate group load/save readiness from existing plan readiness. Treat saved `[]` as intentionally empty; seed only on an absent key, never resurrect removed groups on reload. Validate group shapes before use; malformed/unavailable storage gets a visible warning and an in-memory fallback without silently overwriting the malformed stored value. A failed group write must not claim durable success. Keep optional emails in local group storage only; use synthetic values in tests and documented demo usage. This improves the new group path without broadening scope into an unrelated rewrite of existing plan persistence.

| Proposed files | Change |
| --- | --- |
| `tagalong/src/services/types.ts` | Separate Group/GroupMember and optional group selection/snapshot contracts; preserve Member |
| `tagalong/src/services/demo-data.ts` | Synthetic group seeds/theme metadata |
| New `tagalong/src/services/group-service.ts` | Group validation, name suggestions, alias mapping and browser storage adapter |
| `tagalong/src/services/mock-planning-service.ts` | Optional cloned member/group snapshots for creation; preserve one-off creation |
| `tagalong/src/features/planning/store.tsx` | Group state and create/edit/archive/remove operations |
| New `tagalong/src/features/planning/group-editor.tsx` | Shared member-row/theme/name editor usable in existing dialog flow |
| New `tagalong/src/features/planning/groups.tsx` | Group cards, active/archived filters and lifecycle confirmations |
| New `tagalong/src/app/groups/page.tsx` | Groups route |
| `tagalong/src/features/planning/create-plan.tsx` | Choose existing group/create new/one-off participants |
| `tagalong/src/components/shell.tsx` | Groups navigation and route label |
| `tagalong/src/components/ui/dialog.tsx` | Optional close-autofocus callback for the new groups editor; existing callers retain default behavior |
| `tagalong/src/app/globals.css` | Reuse existing cards/dialogs; minimal responsive group styles |
| New `tagalong/tests/groups.spec.ts` | Group creation, selection, persistence and lifecycle acceptance coverage; retain existing planning.spec.ts regressions |
| `tagalong/tests/planning.spec.ts` | Wait for an actual assistant response before leaving Chat; use the visible board/mobile menu for existing assertions |
| `tagalong/README.md` | Demo group behavior/storage and limitations |

## Actionable implementation order and acceptance

**Inferred proposal — execution sequence:**

1. After execution approval, run lint/typecheck and the existing Playwright suite as baseline. Record exact results; distinguish existing failures from regressions. Do not upgrade packages or alter owner edits to fix baseline issues without an evidenced scoped plan. Coordinate production build separately from the owner's running server so verification does not disrupt their walkthrough.
2. Implement types, synthetic groups and group-service validation/persistence. Preserve old plan serialization and fixtures; do not reset storage.
3. Extend provider with group state/commands and guarded snapshot-based plan creation. Keep legacy create calls valid and plan updates unchanged.
4. Build the shared group editor and Groups page, then wire existing create-plan entry points and desktop/mobile navigation. Scope CSS to groups plus the minimal mobile-nav adjustment; no shared Dialog behavior changes.
5. Add acceptance scenarios using the existing Playwright framework. Re-run lint/typecheck/build and complete desktop/mobile acceptance coverage; manually review narrow layout, field labels, tab order, cancel/confirm focus and draft preservation when browser access is available. Record actual results and remaining limitations before handoff.

| Proposed acceptance check | Regression/requirement protected |
| --- | --- |
| Existing three planning scenarios pass on desktop/mobile | Create/chat/vote/reload, preferences, discover, itinerary and one-off polls remain functional |
| Existing plan key populated before startup; unchanged after group-only actions | Legacy data survives; group lifecycle cannot rewrite plans |
| Preset/custom theme and editable unique name; case/space duplicates and numeric suggestions | Easy identification without relying on labels as IDs |
| Required alias; optional email and expanded name fields; duplicates/invalid email/limits | Minimal predictable group validation; no hidden truncation |
| Selected and inline-created groups flow into new plans; cancellation preserves the draft | All creation paths work without nested form submissions or lost inputs |
| Contacts absent from Plan snapshots and assistant inputs | Group contact details do not spread into planning data |
| Edit/archive/restore/remove group after plan creation | Existing participants, chat and votes stay unchanged; archived groups cannot start new plans |
| Remove all groups, reload; corrupt key and storage failure cases | No seed resurrection or misleading persistence claims |
| Groups route and five mobile navigation items fit narrow viewport | Existing navigation remains reachable and keyboard accessible |

**Inferred proposed commands:** `npm run lint`, `npm run typecheck`, `npm run build`, `npm test`. Browser installation, if missing, requires separate approval. Current Playwright config reuses a localhost:3000 server outside CI, so verify that it is the intended local checkout before testing and use isolated browser contexts with synthetic data. No live APIs are required. [scripts](../tagalong/package.json:5), [Playwright config](../tagalong/playwright.config.ts:2).

**Inferred risks/limits:** Browser-only groups are neither synced nor authenticated; the owner is a demo label. Adult-alias instructions reduce accidental collection but do not provide automatic detection of children's names. Group selection must copy member objects to prevent edits propagating to past plans. Preserve existing local plan data and current owner edits to package/config files. No backend/schema or deployment changes are proposed.

## Implementation and verification — November 6, 2026

**Owner approval:** “Plan approved,” with an explicit request to match existing visual styling. Subsequent explicit approval covered `npx playwright install chromium`. No external credentials were used or stored, no packages/lockfiles changed by this feature, and no production deployment or migrations occurred.

**Observed implementation:** `/groups` and navigation, three synthetic starter groups, shared adult-member editor with optional details, preset/custom themes, unique editable suggested names, archive/restore/removal, group selection and inline creation in the existing plan dialog. Group storage and validation live in [group-service](../tagalong/src/services/group-service.ts); independent state and plan snapshots in [store](../tagalong/src/features/planning/store.tsx); editor/page in [group-editor](../tagalong/src/features/planning/group-editor.tsx) and [groups](../tagalong/src/features/planning/groups.tsx). [Types](../tagalong/src/services/types.ts) preserve legacy Member and plan data compatibility. Existing [Button](../tagalong/src/components/ui/button.tsx), [Dialog](../tagalong/src/components/ui/dialog.tsx) and [Avatars](../tagalong/src/features/planning/shared.tsx) are reused. Existing CSS colors/font/breakpoints are retained; scoped group styles and small navigation overflow fixes blend into the current UI.

**Observed checks:**

- Baseline `npm run typecheck` passed. Baseline `npm run lint` failed before source linting: `eslint-config-next/core-web-vitals` cannot be resolved by the current ESM configuration. Installed Next is 16.4.5 and ESLint config is 15.5.29, reflecting existing owner edits. No dependency/config changes were made to resolve this separate issue. An optional temporary legacy-compatibility lint attempt also failed in old plugin APIs; it is not a lint pass.
- Initial sandbox browser startup failed with EPERM; permitted execution outside the sandbox reached localhost. Playwright's test browser was initially missing. The owner approved its download; final verification uses the normal project config and downloaded Chromium, not a required workspace override.
- `npm test -- --workers=2`: **20 passed (11.6s)**, seven group scenarios plus three existing planning scenarios on desktop and mobile. Coverage includes alias-only plan snapshots, existing-plan preservation, optional contacts, inline creation/draft retention, duplicate/invalid input, archive/restore/removal, empty/corrupt/unwritable storage, keyboard focus and 320px navigation.
- Existing planning tests were adjusted to wait for the real simulated reply before unmounting Chat, view the full board on mobile and open the mobile menu for About navigation. These preserve the original functional assertions rather than hiding failures. Small explicit accessible labels were added to the plan kind controls. New group dialogs restore focus through an optional callback; existing dialog consumers retain default behavior.
- Desktop Groups and mobile editor screenshots from the acceptance suite were inspected: existing Arial typography, coral primary actions, muted background/cards, rounded controls and avatars match the surrounding app. Screenshots are optional ignored test output, generated by `tests/groups.spec.ts`.
- `npm run build -- --webpack` passed in an isolated temporary source copy with installed dependencies linked, to avoid changing the owner's running dev artifacts. Build produced `/`, `/discover`, `/groups`, `/itinerary`, `/plans/[id]`, `/welcome` and the not-found route. Final source checks are recorded at handoff below.
- Final handoff checks: `npm run typecheck` passed; repeated isolated `npm run build -- --webpack` passed against the final source; `git diff --check` passed. Static search found no `workspace/` references in application source, tests, package manifest or Playwright configuration. Pre-existing owner package/config edits were preserved.

**Observed reproducible setup:** Normal installation and test commands remain in [README](../tagalong/README.md). `workspace/` is never imported by the application or tests. To reproduce isolated build verification without touching the live dev output, create an empty temporary directory outside the repository, copy `src/`, `public/`, `package.json`, `package-lock.json`, `tsconfig.json`, `next-env.d.ts`, `postcss.config.mjs` and `eslint.config.mjs` from `tagalong/`, link the installed `tagalong/node_modules` as that directory's `node_modules`, then run `npm run build -- --webpack` there. Do not copy env files. This optional staging directory is not a required application artifact; a normal checkout can run the same build command directly when it is not serving the demo.

**Inferred remaining limits:** This remains browser-local demo functionality. Alex is a fixed persona, not authenticated group authorization; emails are stored locally only and invitations are not sent. Text instructions cannot automatically determine a person's age. Lint/toolchain repair is a separate evidenced follow-up; connected-backend integration and production readiness are not claimed.
