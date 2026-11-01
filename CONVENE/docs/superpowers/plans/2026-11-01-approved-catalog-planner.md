# Confirmed brief to approved catalog recommendations

User-approved next milestone: use the published PostgreSQL directory to match
venues/decorators against the confirmed brief, show reasons/contacts/unknowns,
save a shortlist and prepare reviewable inquiry drafts. No messages or bookings.

Ruling: comparing public approved records inside the owned browser session is a
separate `compare_catalog` capability after brief confirmation. It does not grant
external research, provider communication or cross-device saving; those retain
their account/consent gates. This implements the user's latest agreed flow while
Google setup is pending. Record the distinction in UI/API docs.

1. TDD deterministic matching: full headcount, category/location, published price
   floors, missing capacity/costs, insufficient approved options and food gap.
2. Add catalog action binding to durable six-node graph; cache by owner/event/
   brief version and published directory revision. Recheck publication before
   using cached results or accepting a shortlist action.
3. Implement session/CSRF/owner/version-gated compare, shortlist and draft-preview
   routes. Persist only event-owned state. Group shared office contacts; missing
   verified email means draft-only/no recipient, never guessed send addresses.
4. Supply current approved provider context to conversational RAG only after
   confirmation. Exclude suspended/superseded vendors and stale assistant evidence.
5. React options/workspace: confirmation triggers comparison, sources/contacts,
   candidate/conditional/rejected reasons, shortlist and draft preview. Corrections
   clear stale results. No web tools in this normal flow.
6. Gate legacy live web routes behind an explicit operator setting; keep keyless
   synthetic/demo tests and local legacy catalog separate.
7. Run actual full Pytest, Node/build and HTTP workflow checks; independent review
   of freshness/ownership/approval boundaries; document remaining Gmail/account limits.
