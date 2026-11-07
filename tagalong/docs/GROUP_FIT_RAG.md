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

The authenticated endpoint constructs a plan-scoped retrieval query from the option, category, destination, dates and **confirmed** preference labels. It attempts semantic retrieval in the current plan's `tagalong:<plan-id>` Pinecone namespace. Retrieved IDs are checked against current saved source versions; deleted, stale and other-plan evidence is excluded. Duplicate vector chunks from one source are reduced to that source's best match and the highest relevance matches are considered first. Current Notes and conversation excerpts are also supplied directly, so recently saved context is usable before indexing finishes. The response distinguishes direct database facts, saved Notes, recent conversation, current decisions, user-entered option text, and Pinecone results.

The UI reports whether current source versions are indexed, pending or failed. It reports counts only; it never exposes a Pinecone vector as if it were readable source text. A pending/failed state means older conversation may be missing, while current plan facts and Notes can still be included. Authoritative facts and voting remain in Supabase/Postgres: vector retrieval cannot overwrite the recorded budget, vote totals or confirmed decision state.

OpenAI receives a bounded option description, current facts, verified group excerpts and public place results, then returns a structured per-option comparison. Each match or conflict must individually cite the option's own public listing and the specific group evidence (or authoritative plan fact) supporting that claim. The backend rejects unknown or split-across-findings citations, and clears group-based matches/conflicts when there is no supporting group evidence. The UI places the comparison next to each option and links every finding back to its evidence origin. Group suggestions are ordered by fit verdict, not a fabricated percentage. The backend also enforces an explicit proposed-cost-over-budget conflict from authoritative plan facts. User-entered option details remain unverified and are not presented as venue verification.

When historical retrieval is unavailable, the result discloses that limitation and can still use current Notes and plan facts. Truncated evidence is disclosed. Citation validation checks that every finding points to the required source IDs; it cannot prove the language model's interpretation logically follows from the cited text, so members should review the excerpt. Missing information must remain uncertainty; the result cannot certify allergens, current prices, opening hours, availability or reservations.

### Evaluation and limits

`backend/tests/test_research.py` includes a deterministic ablation: the same synthetic restaurant is compared with saved group context, then the unique saved preference note is removed. With the note, the AI adapter returns a cited fit and the option ranks accordingly; without that evidence, the backend produces `needs_info` instead. This demonstrates that the retrieval evidence can change the output in the test scenario. It is a contract/behavior test, not a measurement of real-world retrieval precision or proof that Pinecone alone is uniquely necessary: current Notes are also available directly for freshness, and the saved memory may overlap PostgreSQL-backed sources. The current purpose of Pinecone is semantic discovery of relevant plan history, not storage of votes or facts.

Summaries, votes, consensus, plan progress and current decisions continue to use structured Postgres data and their dedicated workflows. They are not called RAG just because the app also has Pinecone. Do not use vector retrieval to calculate a tally, decide whether a preference is confirmed, or establish factual state.

### Feature-by-feature classification

| Feature | Classification | What grounds it |
| --- | --- | --- |
| Group fit for a proposed restaurant, stay, or activity | ✅ Strong RAG | Retrieves plan-specific saved evidence before generation; each group claim cites validated group evidence, and removing a unique preference changes the ablation result. |
| Discovered-option comparison with group context | ✅ Strong RAG | Combines current plan evidence with the public option snippet; the card shows match/conflict/unknown findings and links to both sources. Public search itself is not RAG. |
| Recall of older plan discussion | ⚠ Weak RAG | Pinecone can surface relevant messages/Notes, but recent content and current Notes are also read directly; there is not yet a separately measured Pinecone-only benefit. |
| AI discussion or decision summaries | ❌ Not RAG | Uses current plan messages/structured decision context through its summary workflow; no Pinecone retrieval step is used. |
| Consensus, votes, participation, progress, and finalization | ❌ Not RAG | Calculated from current Postgres-backed ballots and decision state. |
| Confirmed user preferences and previous decisions | ❌ Not RAG | Current structured values are read directly from the plan repository; pending proposals do not become facts by retrieval. |
| Contextual comments and recent discussion | ⚠ Weak RAG | Recent messages/comments may be selected directly and older messages may be retrieved semantically for an assessment; comments remain source evidence, not votes. |
| Activity ideas and venue discovery | ❌ Not RAG by themselves | Public search/tool results or model generation can supply candidates. They become RAG-backed only when the separate cited group-fit assessment uses retrieved group evidence. |
| User history across different plans or voting patterns | ❌ Not RAG | Cross-plan retrieval or behavioral personalization is intentionally not implemented. |

## Boundaries and contributor guide

The request is read-only. Membership, suspension, workspace mode, revision and source versions are checked before the result is returned. Option URLs are not fetched by this endpoint, and submitted content is treated as untrusted data. Rate and concurrency limits bound provider use. Results are not automatically stored or indexed.

Backend implementation: `backend/tagalong/group_fit.py` and the configured AI provider. Frontend implementation: the Group fit feature and typed service. See [CONTRIBUTING.md](../CONTRIBUTING.md) for development and required checks. Credential-free tests use synthetic retrieval and provider adapters; those do not establish production retrieval quality. A live synthetic provider smoke check should be reported separately from mocked integration tests.
