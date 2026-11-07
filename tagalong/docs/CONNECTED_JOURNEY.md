# From an idea to an agreed plan

Tagalong now has four primary plan sections: **Overview, Decisions, Chat and Itinerary**. Existing links to Discover, Documents, Polls, Group fit and Demo bookings still work. Those features are contextual tools under **More planning tools**, rather than additional main tabs. Existing plans, polls and votes are retained; legacy votes are not silently converted into current decision consent.

## A complete option workflow

1. Open a decision, such as Lodging, Place or Activities.
2. Choose **Add option** to enter a name, public website, estimated per-person cost and notes. The owner adds voting alternatives; members can use **Find options → Add your own → Suggest in comments**.
3. Alternatively choose **Find options**, describe the need and enter a location. The request retrieves authorized saved group evidence and searches external sources for individual venues. Articles can support research but are not presented as selectable venue options.
4. Inspect **What Tagalong actually used** and **From your group**. Receipts describe completed, unavailable or skipped operations. They are execution records, not private model reasoning or simulated progress.
5. Explore a venue's website or select **Does it fit our group?**. The fit check explains supported matches, conflicts and unknowns against current plan facts and saved evidence. It cannot certify safety, availability or unanimous agreement.
6. Review the option, then add it to the decision. Saved research options retain their source URL, retrieval timestamp and unverified excerpt. Editing the name or website clears the association with the original search result.
7. Members respond to the current option version and comment in context. Adding or changing options invalidates previous responses and finalization. Missing replies and objections cannot be bypassed.
8. The owner confirms the selected alternative and reviews the final plan. **Itinerary → Confirmed choices** shows those outcomes with links and estimates alongside the draft schedule. A confirmed group choice is not a booking.

Chat also exposes **Find options**, so users can research a question without leaving their plan. A normal chat message does not implicitly promise that an external search ran; research receipts show which operations actually executed.

## Data and permission boundaries

Research is read-only and plan-scoped. It validates membership and expected revision before providers run and rechecks membership, revision and source versions afterward. Retrieval outages preserve current facts and selected Notes, with an explicit unavailable receipt. External search failures leave a manual-option path. No live provider calls are required for the automated fixture tests.

Structured option details are additive JSON fields; no database migration is needed. Older label-only decisions remain valid. Legacy edits preserve metadata when labels match. Website and image links are validated, estimates remain unverified, and external provenance is explicitly untrusted evidence. Members cannot edit owner-controlled voting options by submitting a suggestion.

Saved research output is not a guarantee that all group constraints were found. Only selected excerpts are retrieved, and truncated contexts are labeled. External photos appear only when supported by their source; missing photos get an honest placeholder.

See [deployment instructions](DEPLOYMENT.md) and [multi-user test scope](MEMBER_JOURNEY_TESTING.md). Real Supabase email delivery, production database persistence and live provider quality are separate from fixture-based browser verification.

## Saved four-friend walkthrough

The saved plan now opens a forty-turn scripted conversation in **Chat**, with Alex, Maya, Sam and Jordan labeled as fictional friends. **Decisions** displays five choice cards directly, including alternatives, initial objections, the scripted AI resolution, four final responses, evidence and photos. **Itinerary** shows the agreed fictional choices and the day-by-day schedule. The modal replay is supplementary; the story is visible in the ordinary plan sections.

The authenticated Home action **Add four-friends demo plan** creates or reopens one saved fictional Austin-weekend template for the account. **View demo story** replays initiation, constraints, disagreements, sourced reasoning, alternative comparisons, four fictional responses per choice and a three-day itinerary. Destination, dates, lodging, restaurant and activity selections have explicit reasons and reference links. Source-linked photos are distinguished from illustrative scenery, and all modeled costs are labeled fictional.

Fictional cast and story votes never become real account memberships, ballots or bookings. Real invited members can view the story under normal plan authorization. The owner still needs real responses to finalize the actual plan. The replay is clearly scripted; **Run live RAG and AI check** makes a separate normal assistant request and saves its actual answer and citations. That button uses configured providers and their quota; it does not run automatically.

The owner-requested demo was saved to the existing Chandra account on 6 November 2026. Only its three fictional documents were explicitly indexed for the live check. The actual Pinecone query returned three source matches, and the actual AI response was persisted with three citations. No synthetic account, real booking, outbound invitation or charge was created; normal configured AI/embedding usage applies.

## Code organization

### Guided city ideas

After **Start Planning**, review the destination and working dates, then choose interests in **What would your group enjoy?** and click **Suggest things to do**. Individual place cards and dated event cards include provider links, source-supported photos when available, evidence and actual search statuses. Select up to eight ideas before creating the reviewed plan. They become explicitly draft itinerary items and an unverified evidence Note, retaining retrieval timestamps and source excerpts.

Existing plans expose the same guide beside **Chat**, with editable city and visit dates. **Propose for group decision** opens the normal option review: owners add voting alternatives and members suggest them through contextual comments. No search result casts votes, confirms consensus or books anything.

`backend/tagalong/city_ideas.py` separates event extraction, validation and bounded search. `/v1/city-ideas` requires authentication and applies rate/concurrency limits. Event names and source dates must occur on a retrieved organizer page and agree with the requested date range. Unknown events and unavailable tools produce explicit empty/unavailable results. This is not live ticket availability; verify details directly. Provider snippets are untrusted evidence. Selected result identities use URL and event date so later searches cannot collide.

A separate live provider smoke check for Austin, April 16–18, 2027 with Food/Music/Outdoors returned five place options and zero verified dated events. Both lookups completed. This verifies provider connectivity, not comprehensive event coverage or future availability.

The Week 2 reference (`Mastering-Agentic-AI-Week2-Session1/Week2-Session1/company_kb_viewer.py`) separates named retrieval/generation stages from rendering. Tagalong follows that separation while retaining its existing application framework:

- `backend/tagalong/research.py`: bounded provider lookup, saved-evidence retrieval, public-place search, option normalization, and the authorized HTTP orchestration.
- `backend/tagalong/providers.py`: existing embedding, retrieval, generation and index operations.
- `src/features/planning/research/`: workbench state/actions and stateless results/evidence/tool-receipt presentation.
- `src/features/planning/demo-story/`: saved story replay and its explicit live-AI action.
- `src/features/planning/decisions/`: consent, contextual comments, confirmation and final review.
- `src/services/`: typed HTTP contracts and demo adapters.

The replaced, unreferenced `PlanCard`, `decisionStatusLabel` and `decisionNextAction` exports were removed after repository-wide reference checks. Active compatibility routes, Discover, Groups, QA administration and older poll data are retained.
