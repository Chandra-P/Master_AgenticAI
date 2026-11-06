# Restaurant demo booking MCP implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development for independent backend/frontend tasks and final review. Work in the existing integration checkout. Do not commit there; coordinator synchronizes scoped files to the repository and publishes the authorized deployment branch.

**Goal:** Demonstrate real MCP search/availability/create/cancel calls with simulated restaurant reservations, explicit confirmation, persistent plan-member-visible records, and no real bookings or charges.

**Architecture:** Existing FastAPI remains the authenticated host. A LangGraph booking graph calls an official Python MCP SDK client connected over stdio to a local stateless restaurant demo MCP server. The child process exposes only four fictional tools and receives a minimal environment, never Supabase/OpenAI secrets. Supabase aggregate state retains server-owned quotes and reservations. No new paid provider or hosted service.

**Tools:** `search_restaurants`, `check_availability`, `create_demo_booking`, `cancel_demo_booking`. Every result includes simulation labels. Fictional restaurants never masquerade as live discovery results. Real MCP initialize/tool discovery/tool invocation are exercised and shown in an activity trace.

**HTTP contract (all plan membership checked before and after external work):**
- GET `/v1/plans/{pid}/demo-bookings` → `{simulation:true,bookings:[...]}`.
- POST `/v1/plans/{pid}/demo-bookings/search` body `{date:ISO,party_size:1..12,city:string}` → `{simulation:true,restaurants:[{id,name,city,description}],trace:[...]}`.
- POST `/v1/plans/{pid}/demo-bookings/quote` body `{restaurant_id,date,time:HH:mm,party_size,city}` → `{simulation:true,quote:{id,restaurant_name,city,date,time,party_size,expires_at,estimated_total,currency},trace:[...]}`. Date must be within plan dates. Server-owned quote snapshots plan revision and user ID; TTL10 minutes.
- POST `/v1/plans/{pid}/demo-bookings/confirm` body `{quote_id,confirmed:true}` → `{simulation:true,booking:{id,reference,restaurant_name,city,date,time,party_size,status:'confirmed',created_by},trace:[...]}`. Reject expired, foreign, changed-plan quotes. Idempotent by quote ID. Create exactly one clearly fictional itinerary activity and increment plan revision once.
- POST `/v1/plans/{pid}/demo-bookings/{booking_id}/cancel` body `{confirmed:true}` → same envelope with status cancelled. Only creator or plan owner may cancel; recheck membership and suspension. Idempotent; retain record/history, remove only its generated fictional itinerary entry.

**Frontend:** Add `Demo bookings` workspace tab and visible entry from chat/itinerary. Search fictional restaurants, choose a time, review a quote, explicit **Confirm demo reservation**, shared confirmations beginning `DEMO-`, cancellation confirmation, and expandable MCP trace. UI always labels **Demo reservation—no real booking or charge**. Current mode has no live availability, real vendors, payment data, emails, or calendar writes. Chat entry makes the demo discoverable; actual tool calls occur only after an explicit demo search/action. No claim that the model independently booked anything.

## Tasks
- [x] Backend: dependency/lock update through uv; red tests; real SDK server/client and LangGraph graph; authenticated durable quote/confirm/cancel routes with bounded rates/state and concurrency/idempotency/stale checks; synthetic protocol smoke.
- [x] Frontend: typed service and component, new tab/entries, explicit selection/review/confirm/cancel, stale account/plan response guards, persistent records and tool traces; red/green browser tests.
- [x] Review authorization, honest labels, subprocess environment, protocol trace authenticity, duplicate confirmations, expiry, cancellation and cross-plan/account isolation.
- [x] Run required backend, lint, typecheck, production build, desktop/mobile and shared tests; inspect UI; update presentation/contributor docs.
- [ ] Sync scoped source, scan secrets, commit/push, verify CI and public rollout. No migrations or real reservation operations.
