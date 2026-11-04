# Confirmed brief to approved options

The React planner on http://127.0.0.1:8001 now compares a parent-confirmed brief
with the current approved PostgreSQL directory. Confirming the brief automatically
loads options below the conversation. Parents can refresh options, shortlist
alternatives and inspect automatically prepared inquiry previews.

This is a browser-session comparison of already-approved public records. It does
not perform external research, grant an authenticated Google identity or send mail.
Google sign-in is still required for cross-device account saving; Gmail connection
and exact inquiry approval remain separate unfinished integrations.

## Matching and budget behavior

- Use only currently published approved IDs/versions, chosen service categories
  and San Antonio location/service-area evidence.
- Venue maximum capacity must cover every child and accompanying adult. Missing
  capacity/location produces a conditional option, not a confirmed suitable venue.
- Exclude a known base/minimum that already exceeds the entire selected-scope
  budget. Do not silently lower attendance or increase budget.
- Show up to five candidates per category, with the actual configured count.
  Current inventory is three venues, two decorators and zero food providers.
- Compare known published base/minimum costs. Missing fees/quotes/servings are
  unknown, never zero. The minimum combination is not an all-in quote or a typical
  local-market estimate. If a selected category has no usable published prices,
  no complete minimum combination is claimed.
- Keep actual availability, seated layout, theme capability, complete fees and
  reservation-securing conditions visibly unconfirmed.

For the current 120-guest venue/decorator example, the published base/minimum
floor is $610 (South San $235 plus Belle $375). This excludes required unknowns
and does not establish a complete party budget, availability or reservation.

## Agent, persistence and freshness

Requirements, Budget, Vendor, Schedule, Creative and Review execute through the
existing LangGraph PostgreSQL checkpointer with `compare_catalog` action binding.
The workflow trace reports the actual completed nodes. Catalog matching itself
is deterministic and keyless; the conversation model interprets parent input and
answers using retrieved approved records. No model-selected web tools are exposed.

`catalog_comparisons` binds the run to owner/event/brief version and the complete
published-directory revision. Completed comparisons reuse checkpoints. Approval
or record-version changes produce a new comparison. Server checks current
publication again before accepting shortlist changes; changing the brief clears
confirmation and prevents the old version's actions.

`event_shortlist` saves parent/event/brief-specific vendor/version/approval choices.
Changed approvals are flagged stale instead of silently updating the choice.
Private provider evidence is additionally bound to vendor/version/approval.
Unlinked old evidence is quarantined from normal chat context. Suspended or
superseded provider evidence is filtered from retrieval and model history, checked
again after model execution, and protected by current-publication checks under
the same per-vendor locks used by administration when saving a sourced answer.

## Inquiry previews

Shortlisting automatically prepares templates from the confirmed event facts.
Facilities sharing one configured organization/office are grouped into one
explicit alternatives inquiry, avoiding three duplicate coordinator drafts.

Only a consistently verified shared email may populate a recipient. Current
venue emails are unverified, so recipients remain empty and the published
phone/contact page is offered. Every preview says **draft — not sent**, has no
attachments, and is not sendable. Viewing or shortlisting never authorizes mail,
accepts pricing, books a room, signs a contract or pays a deposit.

## API

All actions require the owned browser session, CSRF for mutations, the current
`expected_version`, a planning event and confirmation of that version.

- `POST /api/events/{id}/recommendations`: compare current approved records.
- `GET /api/events/{id}/shortlist?expected_version=N`: valid/stale selections.
- `POST /api/events/{id}/shortlist`: vendor_id, vendor_version, selected boolean,
  expected_version; idempotent current-version choice/removal.
- `POST /api/events/{id}/drafts`: grouped unsent inquiry previews.
- Confirm returns `next_action=compare_catalog`; `save_requires_sign_in` separately
  indicates the remaining Google account-saving step.

The `compare_catalog` policy permits this owned confirmed-session comparison.
It does not grant `research` or any communication capability; those keep their
authentication/approval requirements. Ordinary sessions cannot approve or edit
the global directory.

## Legacy tools

The port8000 synthetic/legacy app remains separate. Its live `/party/agent` and
`/venues/research` routes reject valid live requests by default. Only an operator's
explicit `CONVENE_ALLOW_WEB_RESEARCH=true` enables those older local tools. Tests
of their original behavior use explicit opt-in. The legacy page defaults to a
clearly labeled catalog demo and links to the current PostgreSQL planner.

Apply migrations explicitly with `scripts/init_planner_db.py` (and `--test` for
the isolated test database), rebuild frontend and restart the local preview after
Python updates. The hosted/public/mobile application and working Gmail are not
claimed by this milestone.
