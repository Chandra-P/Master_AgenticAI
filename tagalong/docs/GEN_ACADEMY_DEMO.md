# Gen Academy demo package

The narrated video is `artifacts/tagalong-demo/Tagalong_Gen_Academy_Demo.mp4` at the repository root. Generated media is intentionally excluded from Git. Its sibling SRT captions, transcript, source screenshots, narration manifest and synthetic scenario results make the recording reviewable.

## Story and boundaries

Four fictional friends plan Christmas dinner in San Francisco. Maya wants vegetarian food, a $50-per-person budget and step-free access. A $75 proposal triggers a cited budget conflict. A $35 cheese-pizza option remains uncertain where venue details are missing. Updating the saved preference to vegan causes a dairy conflict with current sources. This is recorded from the actual local app using real OpenAI responses and a temporary plan-scoped Pinecone namespace, with an in-memory database and explicit synthetic authentication. Six fictional sources were indexed; the temporary synthetic vector IDs were removed after recording. No production plans, real accounts, payment or external restaurant reservation were created.

The later MCP demonstration uses its separate fictional restaurant catalogue. It illustrates voting, owner review, explicit confirmation, the saved `DEMO-` reference and tool trace. It does not claim the earlier evaluated option was booked. The video labels fictional participants, AI-generated male/female narration, and simulated reservations.

## Measured evidence

See [the live synthetic evaluation](evaluations/2026-11-06-group-fit-demo.md) and its JSON report. Four declared synthetic cases matched their expected verdicts; 12 findings referenced supplied evidence IDs; median observed response time was 2.950 seconds. These small-sample results do not establish production accuracy, citation entailment or retrieval ranking. The report separates deterministic rule/security tests from live model behavior.

## Before presenting

From the public demo home, choose **See four friends plan an Austin weekend** to replay the fictional conversation, objections, option comparisons, votes, saved evidence excerpts and final itinerary without an account. This replay is explicitly scripted and does not make a live model or retrieval request.

To demonstrate configured AI/RAG live, sign in, open the prepared Austin plan and choose **View demo story → Run live RAG and AI check**. The request uses configured providers and quota; the actual reply and returned citations appear in Chat. `Find options` and `Check group fit` are additional connected flows for live search/retrieval. Do not present the scripted replay as the live provider result.

From `tagalong`, run `node scripts/demo-preflight.mjs`. It performs read-only readiness checks and can wake idle services. A successful preflight is a point-in-time check; it does not prevent a free host from sleeping again. Always-on hosting requires the owner to select and fund an appropriate hosting plan. Keep the local MP4 available so judging does not depend on live hosting or network availability.

Use one focused narrative, show a source, change a constraint, and explain the authority boundary: models propose; people decide; backend rules enforce access and confirmation. Do not imply simulated bookings are live integrations or call a handful of synthetic evaluations a general accuracy score.

## Reliability changes

Typing acceptance now prevents an old animation-frame callback from moving the caret in a later draft. Connected reads retry at most once for transient failures; writes never retry automatically. Non-JSON shared-service responses show a clear temporary-unavailable message. These changes have focused regressions in the composer and connected-service browser suites.
