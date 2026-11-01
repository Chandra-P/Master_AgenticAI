# Party Planning Agent - approved follow-up

User accepted connecting the browsing/extraction tools into the planning agent
outlined in chat: research, evaluate fit, compare venue/decorator combinations,
push back on unsupported budgets and replan when constraints change.

Use six LangGraph nodes: Requirements, Budget, Vendor, Schedule, Creative, Review.
Live Vendor uses OpenAI tool calling to choose Keenable searches and public-page
reads, inspect results and decide next tools (bounded six calls/three rounds).
Tools return real results only; source fetch restrictions stay enforced. Review
uses structured model ranking of server-computed candidate combinations; server
rejects invented IDs and over-allowance combinations. Costs/capacity from public
catalog remain dated snapshots, not live quotes even after page reads. Unknowns
and required extras remain explicit. Model planning notes are opinions, not vendor
facts. No bookings, messages or payments. Demo comparison is explicitly catalog
only and makes no external calls. Live failures never pretend to be live success.

Stream actual node/tool activity via NDJSON to the existing website. Show
recommendations, rejected options, unknowns and an apply-combination action.
Invalidate recommendations if party brief changes. No credentials in browser.
Limit worker concurrency, external calls and total elapsed time. Tracing remains
disabled by default. Keep existing API/Streamlit acceptance suite working.
