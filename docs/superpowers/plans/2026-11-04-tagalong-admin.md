# Tagalong app administration implementation plan

**Approved scope:** Separate app-admin authority can coexist with plan owner/member roles. The user requested implementation and multiple stored QA plans for review.

**Architecture:** Server-owned `app_admins`, `suspended_users`, `admin_audit`, and `qa_runs` maps in the existing transactional aggregate. No permissions from user-editable Supabase metadata. Bootstrap grants only a selected confirmed existing account; no automatic first-user admin. Ordinary plan endpoints retain membership checks.

**Dashboard:** `/admin` lists bounded account and plan summaries, ingestion status and audit events. Private plan inspection requires a reason and creates a durable audit event before returning content. Account suspension/restoration is audited; administrators cannot suspend themselves or other administrators. No destructive deletion or role-grant API.

**QA:** An idempotent server action creates three synthetic, clearly labeled plans owned by the requesting administrator, with budgets, polls, messages, tasks, itinerary drafts and source documents. It does not create accounts or invite real people. Plan content and review data remain stored for the user.

- [x] Write failing backend authorization, suspension, audit and QA isolation tests.
- [x] Implement bounded admin endpoints, profile admin flag and additive bootstrap utility.
- [x] Add typed service and admin dashboard, navigation and private inspection controls.
- [x] Verify browser admin/non-admin workflows and existing checks; obtain independent review.
- [x] Bootstrap the confirmed existing user and persist QA plans, checking live providers only on synthetic QA content.
- [ ] Synchronize reviewed source, commit/push existing review branch and document deployment verification limits.

**Review focus:** Admin does not imply membership; ordinary users cannot self-promote; suspensions cover in-flight writes; private content never appears in summary responses; inspection and account actions are atomic with auditing; QA creation retries do not duplicate plans.
