# Architecture

Browser → Streamlit → FastAPI → LangGraph → SQLite → plan response.

1. Requirements validates the structured event brief through Pydantic before the
   graph starts and establishes a plan ID and explicit mode.
2. Budget allocates 45% venue, 45% catering, 10% unspent reserve.
3. Vendor retrieves synthetic candidates, filters city/capacity and chooses the
   cheapest affordable candidate per category. Demo uses local JSON; live uses
   Pinecone semantic matches then validates IDs against that same local catalog.
4. Schedule creates four ordered activities starting at 10:00 local time for the
   supplied duration. Start-time/timezone selection is future work.
5. Creative proposes activities deterministically in demo or through OpenAI in live.
6. Review flags missing categories and requires human checks for accessibility,
   diet, taxes, availability and local time. Even ready plans require human review.

SQLite stores complete plan JSON using parameterized SQL and per-operation
connections. API construction initializes the schema. Lists return the newest 100
plans. Streamlit calls the API and can export JSON; it does not duplicate planning.

No API authentication, production hosting, bookings, payments, calendar writes,
negotiation or autonomous vendor contact. Live model output is advice only and
cannot alter vendor costs or initiate external actions. There is no automatic
revision loop; a user edits the brief and creates another plan.

LangSmith tracing is opt-in via environment variables; it can expose brief content
to the tracing service. Tests force demo mode and disable tracing.

The MVP uses specialist deterministic agents plus live RAG and generation adapters,
not six independent LLM calls. This keeps the November 2 demo reproducible and
makes constraints testable. More LLM reasoning can be added after the demo works.
