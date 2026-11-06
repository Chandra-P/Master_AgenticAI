# Does this option fit our group?

Use **Group fit** inside a shared plan to assess a restaurant, activity, stay or other proposal. You can also start from an individual place in the plan's **Discover** tab. This is an evidence-based review, not a booking or a guarantee that a venue meets every requirement.

## Demo walkthrough

1. Set the plan's working budget and destination.
2. Save Notes describing the group's stated preferences and a menu or option description. Label fictional demo content clearly.
3. Open **Group fit**, enter the option and its details, and optionally supply a proposed cost per person and website link.
4. Run the check. Review what fits, what conflicts, and what still needs checking.
5. Open the cited sources to inspect the supporting excerpts. A budget conflict should cite current plan facts; dietary or accessibility claims should point to the supplied evidence rather than invented facts.
6. Discuss the result and use the existing voting and owner-review flow. The check does not add an itinerary entry, cast a vote, approve a decision or create a reservation.

A useful presentation example is a vegetarian group with a $50-per-person budget evaluating a $75 option. Show the budget conflict and the saved preference evidence, then explain that missing entrance or allergen information remains a question to verify directly with the venue.

## How retrieval works

The authenticated endpoint always attempts semantic retrieval in the current plan's `tagalong:<plan-id>` Pinecone namespace. Retrieved IDs are checked against current saved sources and versions; deleted, stale and other-plan evidence is excluded. Current Notes are also supplied directly, so newly saved documents do not depend on indexing having finished. Authoritative plan facts remain in Supabase/Postgres; a vector match cannot overwrite the recorded budget or turn a pending proposal into a confirmed decision.

OpenAI receives a bounded option description, current facts and verified excerpts. Its structured response separates matches, conflicts and missing information. Finding citations must reference supplied evidence IDs. The backend also enforces an explicit proposed-cost-over-budget conflict. User-provided option details are labeled as unverified evidence, not independent venue verification.

When historical retrieval is unavailable, the result discloses that limitation and can still use current Notes and plan facts. Truncated evidence is disclosed. Missing information must remain uncertainty; the result cannot certify allergens, current prices, opening hours, availability or reservations.

## Boundaries and contributor guide

The request is read-only. Membership, suspension, workspace mode, revision and source versions are checked before the result is returned. Option URLs are not fetched by this endpoint, and submitted content is treated as untrusted data. Rate and concurrency limits bound provider use. Results are not automatically stored or indexed.

Backend implementation: `backend/tagalong/group_fit.py` and the configured AI provider. Frontend implementation: the Group fit feature and typed service. See [CONTRIBUTING.md](../CONTRIBUTING.md) for development and required checks. Credential-free tests use synthetic retrieval and provider adapters; those do not establish production retrieval quality. A live synthetic provider smoke check should be reported separately from mocked integration tests.
