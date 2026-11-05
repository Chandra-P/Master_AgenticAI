# Tagalong private join links

## Intent
Let a plan owner invite people who do not yet have Tagalong accounts by sharing a private link. The user selected this approach instead of invitation emails or requiring existing accounts.

## Approaches
- **Private join link (selected):** the owner copies a link and shares it themselves. Works with new and existing accounts without an invitation email service.
- **Invitation email:** adds delivery configuration and operational dependencies; not selected.
- **Existing accounts only:** current behavior; does not solve inviting new users.

## Proposed behavior
These details are builder recommendations pending design approval:
- An owner can create and copy one active invitation link per plan, replace it, or disable it. Links expire after seven days. Replacing a link invalidates the previous link.
- Anyone holding a valid link can join after signing in and explicitly selecting **Join plan**. The interface explains that the link grants membership and should be shared only with intended participants.
- A signed-out visitor can register or sign in, then return to the invitation page. Email confirmation remains part of the existing Supabase signup flow. Returning in another browser requires reopening the original invitation link.
- No plan name, members, messages, or documents are returned before successful authenticated joining. Opening the URL alone never joins a plan.
- Joining adds normal member access through the existing transactional membership rules. Repeated acceptance by a current member is idempotent. Expired, disabled, malformed, and replaced links show an actionable unavailable-link message.
- Removing a member does not disable the shared link; owners must disable or replace it to prevent that person rejoining. The sharing interface explains this.

## Implementation constraints
- Keep Next.js, FastAPI, Supabase authentication, and the existing Postgres transaction model.
- Generate at least 256 bits of random token entropy. Persist only a SHA-256 digest and expiration in server-owned state; never include invitation records in plan views or mutable client plan patches.
- Place the token in the URL fragment, read it on the join page, and submit it in an authenticated POST body. Do not put tokens in query strings, server logs, analytics, or browser persistent storage. Clear the fragment after successful joining.
- Preserve the fragment while navigating through account setup in the same tab, using session-only browser state cleared on success or abandonment. Never automatically accept after authentication.
- Owner-only create/replace/revoke endpoints and authenticated acceptance execute authorization and membership changes atomically. Use existing member limits and revisions. Bound input and rate-limit acceptance attempts.
- Invitation metadata lives in an optional aggregate-state map, defaulting empty for existing databases; no destructive migration or account provisioning is needed.
- Existing email-based member addition remains available with a clearer account-not-found explanation. Do not send invitation emails or create accounts on behalf of recipients.

## Verification
Backend tests cover owner authorization, opaque token storage, expiry, replacement, revocation, member limits, repeat acceptance, concurrent acceptance, protected state, and unauthenticated requests. Browser tests cover copying a link, signed-out arrival, authentication return, explicit joining, invalid links, and visibility of the shared plan to a second account. Run the repository-required frontend and backend checks before delivery. Local test authentication is not evidence of live Supabase signup behavior.

## Delivery
Implement and review in the existing isolated integration checkout, synchronize reviewed source into the workspace, and commit to the existing review branch. Verify deployment health and invitation behavior after Render deploys. Production signup confirmation delivery remains dependent on the configured Supabase email service.
