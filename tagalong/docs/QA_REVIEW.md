# Saved QA plans for administrator review

Created November 4, 2026 (America/Chicago), with the user's authorization. These are synthetic scenarios stored in the real Tagalong database and owned by the existing user account. That account has a server-owned app-admin grant, independent of its plan memberships.

| Saved plan | Budget per person | Focus |
| --- | --- | --- |
| [Chicago dinner](https://tagalong-web-clbe.onrender.com/plans/8bcf3564-c1c2-4594-af8d-193e101c11c7) | $65 | Vegetarian dinner, budget, date/pacing polls |
| [Austin weekend](https://tagalong-web-clbe.onrender.com/plans/432b121c-8412-4ce3-add4-caad6fb4834e) | $350 | Relaxed pace, free outdoor activities, weekend planning |
| [Toronto city break](https://tagalong-web-clbe.onrender.com/plans/b40c84b3-eed0-4d44-a139-c75bed306862) | $500 | Step-free access and clear limits on venue availability |

Each plan includes a QA brief document, synthetic conversation, voted poll, draft itinerary, and tasks. No extra auth accounts, real invitations, reservations, or calendar events were created. Live OpenAI responses, Pinecone document retrieval, current-budget grounding, document citations and same-plan source isolation passed for all three scenarios. Actual model responses and proposed preferences remain stored for review. The tests do not establish who changed a historic budget; budget-change attribution is not implemented.

The authenticated admin dashboard is `/admin`. It lists summaries, accounts, ingestion job counts and the most recent audit entries. Private plan inspection requires a reason and is logged. Ordinary plan participation still requires membership, even for an admin. The QA creation button is idempotent for each admin and reuses their saved review plans.

Sign in as **Admin** to review these QA plans. When signed in as **Member**, even their owner cannot list or open them. Normal member plans remain separate. The new **Planning demo stories** library contains the presentation-focused San Francisco Christmas, Yosemite and San Francisco date-night conversations; these are distinct from the retained live-provider QA records above. Storyboards are scripted fictional illustrations and explicitly labeled as such.

## Verification limits

Backend and desktop/mobile browser tests cover authorization, admin/member separation, account suspension/restoration, stale-state clearing, invitations, documents, chat, voting, preference confirmation, and plan refresh. Browser multi-account tests use explicit test-only auth and in-memory storage. Live provider checks used only these synthetic QA scenarios against real Postgres, OpenAI and Pinecone; they did not create or impersonate a second real Supabase account.

The admin frontend/API changes require deployment of the current review branch to both Render services. The admin grant and QA records already exist in Postgres. At the last check before this update was pushed, the hosted API was healthy and `/admin` was still returning 404 because it had not received this feature. Hosted indexing remains external until `TAGALONG_EMBEDDED_WORKER=true` is enabled on the API service.
