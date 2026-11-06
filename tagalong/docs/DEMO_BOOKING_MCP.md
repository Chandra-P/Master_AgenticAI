# Restaurant booking demonstration with MCP

This is a real MCP integration with a fictional reservation provider. No restaurant, payment processor, email service, or calendar is contacted. Every result and the UI identify **Demo reservation—no real booking or charge**.

## Architecture

`Workspace demo action → authenticated FastAPI route → LangGraph mcp_tool node → official MCP Python SDK client → stdio → fictional restaurant MCP server`

The backend launches a fixed local Python server using the official `mcp` SDK (locked to 1.30.0). Each operation performs actual MCP initialization, tool discovery, and tool invocation. The UI displays the returned activity trace. This is backend-driven orchestration following an explicit user action; it is not an OpenAI model independently choosing or completing a real booking.

Tools:
- `search_restaurants`: three explicitly fictional restaurants, with demo time choices.
- `check_availability`: simulated availability and a fictional USD estimate; unsupported time slots are unavailable.
- `create_demo_booking`: a deterministic `DEMO-…` reference for an approved quote.
- `cancel_demo_booking`: a simulated cancellation acknowledgment.

The stateless MCP child never stores plan state. FastAPI retains server-owned quotes and reservations in the existing Supabase aggregate. Quotes expire after ten minutes and are tied to the requesting user and current plan revision. Confirming creates one explicitly fictional itinerary entry. Retrying a successful confirmation returns its original record. Cancellation retains the record and removes only its generated itinerary entry. A cancelled quote cannot recreate a booking.

Only current plan members can search, quote, confirm or view records. Only the booking creator or plan owner can cancel. Authorization, suspension, date bounds, quote ownership and revision/expiry are checked around tool calls. SDK subprocess defaults inherit only an OS environment allowlist plus the explicit process setting; provider and database credentials are not forwarded. This is not an OS filesystem sandbox. Two concurrent child-process slots and bounded operation timeouts protect the existing host.

## Demo walkthrough

1. Sign in and open a shared plan. Use the **Demo bookings** tab or **Try demo restaurant booking** in chat. Local browser demo mode requires signing in before this real protocol flow can run.
2. Enter a city, a date within the plan, and party size. Click **Search fictional restaurants**.
3. Select a fictional restaurant and a displayed demo time, then **Review demo reservation**.
4. Show the estimate and quote expiry. Nothing is saved as a reservation yet.
5. Click **Confirm demo reservation**. Show the `DEMO-…` reference, shared record, and fictional itinerary activity. Expand **MCP activity trace** to show the actual protocol calls.
6. Refresh to demonstrate persistence. Another member can view it; cancellation is restricted to creator/owner.
7. Click **Cancel demo reservation**, then **Confirm cancellation**. The cancelled demo record remains visible, while its generated itinerary entry is removed.

Live Discover results are separate from the fictional booking catalogue. Do not present a demo confirmation as a reservation at a real venue found through search.

## Local development

From `tagalong/backend`, run `uv sync --frozen`. The server can also be launched by an MCP host as `uv run python tagalong/demo_restaurant_server.py` over stdio. Tagalong's gateway launches that fixed script with the same environment's Python executable. No extra hosted service or vendor account is required.

Run `uv run pytest tests/test_demo_bookings.py -q`. It includes actual SDK initialize/discovery/four-tool calls, plus route authorization, stale/expired quotes, concurrency, idempotency and cancellation checks. `npm run test:shared` exercises the real protocol through the desktop/mobile UI with synthetic local accounts and in-memory state. It does not create production users or real reservations.
