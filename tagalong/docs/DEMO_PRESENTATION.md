# Tagalong: from scattered conversation to an agreed plan

## Opening: the problem people recognize

“Everyone wants the trip. Nobody wants to coordinate it.”

Show a fictional group chat with one person asking about dates, another proposing a place, someone changing the budget, and a dietary preference buried in the conversation. End with “So what did we actually decide?” The problem is fragmented decisions and coordination effort; do not claim measured time savings without a study.

## Before and after

| Current planning experience | Tagalong-assisted experience |
| --- | --- |
| Ideas distributed across conversations and notes | A shared plan with conversation, documents and planning board |
| Repeated questions about dates, budget and preferences | An assistant can summarize supplied context and retrieve relevant earlier evidence |
| Suggestions mistaken for decisions | Preference proposals require explicit confirmation |
| Group disagreements remain unresolved | Polls record each member's current vote |
| Someone manually gathers the final outline | A shared itinerary and tasks make the draft and next steps visible |

## Demonstration: start to finish

Sign in as **Admin**, open the admin dashboard, and select **Planning demo stories**. Each scenario has Previous/Next, Show complete conversation and Replay from start controls. The evolving plan panel updates with the conversation: budget, preferences, votes, draft itinerary and assigned checks. These are curated fictional storyboards with scripted AI illustrations, not recordings of real users or live model runs.

1. **Christmas weekend in San Francisco:** Shyam Srinivas and Arjun begin with a vague December 25–27 idea. They establish a sample $600 per-person cap, vegetarian meals, public transport and a relaxed pace. The AI illustration organizes constraints, compares directions and drafts the itinerary after both friends vote. They explicitly agree and assign remaining price/opening-hours checks.
2. **Three days in Yosemite:** Shyam, Arjun, Neha and Kavya have different activity preferences. The story shows how the group chooses optional paired activities, preserves gentle alternatives and a fallback, and agrees to an illustrative $450-per-person outline. Access requirements, conditions, suitability and actual costs remain to be verified.
3. **San Francisco date night:** Shyam and Priya clarify that the sample $180 cap is for both people, not per person. The conversation reconciles a quiet dinner, vegetarian options, an optional walk and a 10 pm finish. Both approve an outline with clear responsibilities and no booking claims.

The synthetic names, dates, prices and conversations exist for demonstration only. Holiday openings, weather, park access, venue availability and prices have not been verified. There are no real invitations, bookings or calendar writes in these stories.

## Show live AI separately

After the curated story, clearly announce a live assistant demonstration using an approved synthetic QA plan. The existing QA plans contain retained real OpenAI/Pinecone checks for budget grounding and document citations. Mentioning `@Tagalong` in a connected plan calls the live assistant; the local browser demo uses scripted responses. Do not present a curated story as proof that a model generated that exact conversation or that all its proposed workflow automation exists in the live app.

## Explain the architecture briefly

Next.js presents the shared workspace. FastAPI validates Supabase sessions and plan membership. Postgres stores authoritative plan state. LangGraph routes assistant requests, OpenAI generates structured suggestions and embeddings, and Pinecone supplies plan-scoped retrieval. The assistant proposes; people approve decisions. Discover also supports explicit Keenable web search with clickable source links. These snippets do not establish venue prices, hours or availability; the assistant does not automatically invoke this search. Booking and calendar integration remain disabled.

## Finish with the outcome

Show the agreed outline next to the opening conversation: a visible budget, confirmed preferences, recorded votes, a draft itinerary and assigned next steps. Then switch to **Member** mode: the admin dashboard, curated stories and QA plans disappear, while normal owned/shared plans remain. Admin status and plan ownership are independent; selecting Admin never grants authority to an unauthorized account.
