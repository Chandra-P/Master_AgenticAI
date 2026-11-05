# Private join links implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement task by task.

**Goal:** Owners share revocable seven-day links that authenticated recipients explicitly accept.
**Architecture:** Store token digests in the existing transactional aggregate. Next.js reads fragment tokens and holds them in session storage during account setup. Existing membership projections enforce access.
**Tech Stack:** Next.js, TypeScript, FastAPI, Postgres, Supabase.
**Spec:** `docs/superpowers/specs/2026-11-04-tagalong-private-join-links-design.md` (approved).

## Global constraints
No invitation emails, account provisioning, raw token persistence on the server, or pre-join plan disclosure. Keep existing member limits and owner authorization. Seven-day expiration; replacement and disabling invalidate outstanding invitations. Use the existing isolated integration checkout.

## Review focus
Authentication return must retain the invitation without auto-joining; a replaced token must fail; concurrent joins must not duplicate membership; client patches must not alter invitation state; removal must explain possible rejoining while a link is active.

### Task 1: Server invitations
- [ ] Add failing tests in `tagalong/backend/tests/test_invitations.py` for owner-only create/revoke, authentication, token digest storage, expiry/replacement/revocation, idempotent and concurrent joins, member limits, and protected state.
- [ ] Run targeted pytest and confirm failure before implementation.
- [ ] Create `backend/tagalong/invitations.py` helpers and wire POST/DELETE `/v1/plans/{pid}/invitation`, POST `/v1/invitations/accept` accepting `{token}` and returning `{plan_id}`. Use bounded tokens and per-account acceptance rate limits.
- [ ] Run backend pytest.

### Task 2: Sharing and account return
- [ ] Extend `src/services/connected.ts` with invitation methods; create `src/features/planning/join.tsx`, `src/services/invitation-session.ts`, and `src/app/join/page.tsx`.
- [ ] Update account UI to offer returning to a pending invitation after sign-in; preserve explicit acceptance.
- [ ] Add owner create/copy/replace/disable controls in workspace sharing dialog, including expiry and rejoining guidance.
- [ ] Cover fragment retention and explicit join in browser tests; run lint, typecheck, build, demo and shared suites.

### Task 3: Review and delivery
- [ ] Independently review authorization and token handling; resolve findings.
- [ ] Update deployment/status docs; synchronize scoped source to workspace without credentials or build output.
- [ ] Commit and push the review branch; verify CI and deployed behavior where accessible. Report any remaining deployment or real-auth verification requirements precisely.
