# Group-based plan access and in-app notifications

Status: owner approved November 9, 2026; implementation and local verification complete on `GroupShare`. Ready for a pull request targeting `main`; production deployment remains unverified.

## Confirmed requirement and boundary

Owner selected in-app notifications and a plan in each member's list. No email or other outbound messaging. Connected workspace only; preserve demo behavior. This extends GroupShare's group visibility feature, which intentionally does not grant plan membership.

**Observed:** `backend/tagalong/core.py:create` stores only the creator in plan membership even when `plan_group` supplies a roster snapshot. Generated-draft acceptance in `backend/tagalong/coordination_routes.py` uses that same creation helper. `src/features/planning/group-picker.tsx` explicitly describes intended participants rather than membership. Existing member removal is owner-only in `backend/tagalong/app.py`.

## Approved behavior

1. In manual creation and generated-draft review, show a recipient review when an owned group is selected. The owner explicitly selects **Share this plan with group members**; leave it unchecked initially. Explain that recipients receive normal plan participant access (view, chat, vote), while owner controls remain owner-only. List aliases without account emails as unable to receive automatic access.
2. Save approved recipient emails privately with the plan-sharing intent, outside the public plan snapshot and AI inputs. Authenticate and verify the member's current email on their next authorized session/refresh before redeeming that intent into real account membership. This supports verified accounts that have not previously signed in to this app, without scanning an external account directory or trusting a stale actor cache. Deduplicate membership and notifications; enforce normal member limits and suspension rules.
3. Once redeemed, the plan appears through the existing authorized plan list, and a connected-only notification indicator lists **A plan was shared with you** with an Open plan action and read/unread state. Only the recipient can read/mark their notifications. Deleted or inaccessible plans must not disclose stale titles through notifications.
4. For existing plans, the owner can explicitly **Share with group** from the member-management flow: choose an owned active group, review its current roster and confirm. Require current plan and group revisions. Do not silently backfill historical plans or rewrite their original group snapshot.
5. Snapshot recipient approval: later group edits, archive/unshare or deletion do not silently change existing plan membership. Owners manage plan access separately. Removing a plan member must invalidate that recipient's corresponding pending grant so refreshing cannot silently rejoin them. Pending grants need owner-visible revocation as well. Only a newly reviewed sharing action can restore access.

## Files and state

- Backend: `core.py`, `app.py`, `models.py`, `coordination_routes.py` and draft request models; new focused `plan_group_sharing.py` and `notifications.py` modules. Keep group viewing permissions separate from plan access.
- Frontend: group picker, manual creation, generated-draft review, workspace member management, service contracts/client and store; connected-only notification component in `src/components/shell.tsx`. Reuse existing visual tokens/dialogs.
- Persistence: backward-compatible private sharing intents and per-account notification/read state inside existing PostgreSQL JSON state; existing membership projections provide normal RLS/revision behavior. No SQL migration expected. Add explicit record limits and idempotent redemption.
- Docs: update group sharing/plan behavior and record actual checks. App/tests must remain independent of `workspace/`.

## Acceptance and checks

- Owner shares a plan from both creation paths; a matching verified account sees it in its list and gets one durable notification, including across refresh/sign-in. Nonmatching, unverified and alias-only users receive no access.
- Existing-plan sharing is explicit, owner-only and rejects stale roster/plan revisions. Creation without approval remains private. No-email aliases are clearly reported rather than silently called invited.
- Members can participate normally but cannot use owner-only actions. Notifications are isolated by account, read state persists, and revoked/deleted plans do not leak through the feed.
- Removing members/pending recipients prevents automatic reentry. Group edits do not retroactively alter approved plan participants. Retries do not duplicate people or notifications; account switches ignore late responses.
- Run backend tests, lint/typecheck/build, frontend regressions and shared browser tests using synthetic local auth/providers, including demo isolation. No paid calls, production changes, commits or deployments without further instruction.

Primary risks: unintended plan disclosure, implicit permission escalation, stale identity matching and re-granting revoked access. Mitigations: explicit recipient review, trusted verified-email redemption, transactional checks/deduplication and revocable grants. This scope is larger than a cosmetic notification change because it modifies authorization.

## Implementation details

Private JSON keys: `plan_group_grants` (per-plan recipient email snapshots/status), `plan_group_approvals` (review sequence), `plan_group_blocks` (removed account revocation barrier), and `notifications` (recipient/plan/read state). Public plan snapshots and AI inputs contain none of these recipient emails. Existing state without these keys stays valid; no migration is required. Recipient snapshots are limited to the normal plan-member bound per plan, with a global grant limit; notification retention is the latest 200 per account with a global limit. Plan events use the existing bounded audit records without contact emails.

Endpoints: owner GET/POST `/v1/plans/{pid}/group-sharing`; owner DELETE `/v1/plans/{pid}/group-sharing/{grant_id}` for a pending approval; account GET `/v1/notifications` and POST `/v1/notifications/{id}/read`. Manual creation and draft acceptance accept `share_with_group` (strict boolean, false by default) with a current owned group/revision. Draft retries cannot change the accepted sharing approval. Member removal blocks old grants; a new explicit review can restore access. Ownership transfer revokes still-pending grants while preserving existing participants.

Current provider-verified identity is checked during authenticated requests, so pending recipients join on sign-in or their next refresh, rather than an external directory lookup or a background message sender. Membership and notification creation occur in the same transaction. Normal participant rights and membership projections are reused. QA review plans cannot use group sharing. Notification results exclude deleted/inaccessible plans and derive titles only after access checks. Connected UI polls while visible every 15 seconds and refreshes on focus/open; this is not a push/email delivery guarantee.

No required configuration, package, script or fixture is stored in `workspace/`. Provision from the normal repository setup and synthetic local HTTP fixture. Frontend and API changes must be released together. The owner subsequently authorized committing/pushing `GroupShare` and opening a pull request targeting `main`; merging or deployment is not part of that authorization. Private approvals, including revoked records, remain in state; no automatic recipient-data purge was introduced.

## Actual verification — November 9, 2026

| Check | Result |
| --- | --- |
| `npm run lint` | Passed without warnings |
| `npm run typecheck` | Passed |
| `npm run build` | Passed with approved sandbox exception |
| `npm test -- --workers=2` | 166 passed, 4 configured visual-project skips (47.4s) |
| `npm run test:shared` | 76 passed, 4 configured visual-project skips (4.5m); includes 8 new desktop/mobile plan-sharing cases and all prior group-sharing cases |
| Backend `.venv/bin/python -m pytest tests -q` | 290 passed, 1 dedicated-database skip (7.41s) |
| `git diff --check` | Passed |
| Credential-pattern scan | 34 changed/new feature files, no matches for scanned credential patterns |
| Visual inspection | Desktop and mobile in-app notification screenshots inspected |

New backend cases exercise explicit/manual/generated sharing, current verified identity, notification isolation/deduplication/read state, stale revisions, pending revocation, removal without rejoining, unchanged approved recipients after group edits, deletion/suspension, ownership-transfer pending revocation, and capacity rollback. The initial browser run exposed an ambiguous select label and a test auth-mock teardown occurring before logout completed; both were corrected and pass in the complete run. Existing tracked regression screenshots were restored. Dependency manifests, lockfiles and deployment files remain unchanged. No installs, migrations, production verification, paid calls, email, commit or push were performed. Fixtures simulate Supabase and providers; the dedicated real-database skip means live RLS/Realtime behavior is not verified here.
