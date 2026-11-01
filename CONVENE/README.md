# CONVENE

CONVENE is a conversational San Antonio event planner with a React/FastAPI
interface, PostgreSQL-backed approved vendor directory, source-grounded RAG,
versioned event briefs and a durable six-node LangGraph workflow.

## Current approved-vendor planner

Parents confirm a brief, compare approved venue/decorator options, save a shortlist
and review automatically prepared inquiry drafts. Published prices are incomplete
base/minimum snapshots; availability and reservation conditions remain unconfirmed.
The normal planner performs no web scraping and sends no messages or bookings.
Google account saving, Gmail integration and public deployment are still pending.

- [Setup and current limits](docs/public-planner-setup.md)
- [Confirmed brief to approved options](docs/approved-catalog-planner.md)
- [Vendor storage and local approval administration](docs/vendor-directory-admin.md)
- [Verification evidence](docs/verification.md)

The local React planner runs at http://127.0.0.1:8001 after database setup and
`npm run build` in `frontend/`. Local credentials, databases and runtime files are
excluded from Git. The most recent full local suite passed **134 tests**; see
the verification document for actual commands and live HTTP coverage.

## Legacy keyless demo

The original course MVP uses six LangGraph agents through a FastAPI API
and Streamlit UI. Target working end-to-end: **November 2, 2026**.
Submission deadline: **November 5, 2026**.

Synthetic estimates only. No real bookings or payments. All amounts are USD.
Demo mode requires no API keys and makes no external AI or retrieval calls.
The six agents are graph nodes; in demo they are deterministic. In live mode,
Vendor uses OpenAI embeddings and Pinecone RAG; Creative uses an OpenAI model.
Other nodes remain deterministic for predictable constraint checking.

## Windows / VS Code

Open this folder in VS Code. Use Python 3.12 or newer. In PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn convene.api:app --reload
```

Leave the API terminal open. In a second terminal, from the same folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open http://localhost:8501. The API docs are at http://localhost:8000/docs.
Create a San Antonio event with 40 guests and a $5,000 budget. Download the resulting
plan JSON or load saved plans. SQLite persists plans in `data/convene.db`.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

On Linux/macOS, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.
Run all commands from the project root. Do not expose the API publicly: this
course MVP has no authentication, per-user isolation, or rate limits.

## Optional live mode

1. Put your own keys into `.env` (never commit it).
2. Create a Pinecone index with 1536 dimensions and cosine metric; set
   `PINECONE_INDEX` to its name.
3. Run `python -m scripts.seed_pinecone` with your virtual-environment Python.
   This explicitly uploads only the synthetic vendor catalog and incurs costs.
4. Set `CONVENE_MODE=live`, `OPENAI_API_KEY`, and `PINECONE_API_KEY`. Restart API.
5. To opt into traces, set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.
   LangGraph supports LangSmith tracing natively. Traces may contain event inputs;
   use synthetic inputs for the course. Paid services are not required for demo.

Live service failures return an error rather than silently switching to demo.
Vendor matches are checked against the local synthetic catalog; retrieved content
cannot introduce real vendors. Pinecone similarity is not an availability check.

## GitHub handoff

No repository or valid GitHub connection was available at creation time. These
files have not been committed or pushed. Do not assume this cloud folder syncs
to Windows. Download the source ZIP, extract it, and copy the files into your
intended CONVENE checkout (including `.github`, `.gitignore`, `.env.example`).

```powershell
git clone https://github.com/YOUR-ACCOUNT/CONVENE.git
cd CONVENE
# Copy project source here, then verify the remote before staging:
git remote -v
git status --short
git add .
git diff --cached --stat
git commit -m "Build CONVENE six-agent course MVP"
git push
```

Verify the staged files contain no credentials or local databases. Alternatively,
connect the intended repository to this Codex cloud environment to continue here.

## Layout and API

- `convene/models.py`: input validation
- `convene/workflow.py`: six-agent LangGraph workflow
- `convene/integrations.py`: demo catalog and optional OpenAI/Pinecone adapters
- `convene/storage.py`: SQLite persistence
- `convene/api.py`: `POST /plans`, `GET /plans`, `GET /plans/{id}`, `GET /health`
- `streamlit_app.py`: create, view and export plans
- `tests/test_app.py`: API and workflow acceptance tests
- `docs/architecture.md`, `docs/milestones.md`: design and delivery scope

See `docs/verification.md` for actual cloud verification results and limitations.

## Real venue web research

The **Research real venues** section supports automatic discovery, supplied
website URLs, or both. Results show copied venue facts, supporting excerpts,
source links and retrieval times. They are separate from synthetic demo plans
and are not included in the demo's estimated vendor total.

Configure these in an uncommitted `.env` and restart FastAPI:

```dotenv
OPENAI_API_KEY=your-own-key
BRAVE_SEARCH_API_KEY=your-own-key
CONVENE_RESEARCH_MODEL=gpt-4.1-mini
LANGSMITH_TRACING=false
LANGCHAIN_TRACING_V2=false
```

URL extraction needs only the OpenAI key. Automatic discovery also needs a
Brave Search API key. Search and model calls may incur costs. Only city and
guest count are sent to search; readable public page text goes to OpenAI.
Research uses the Responses API with `store=false`; this does not override a
provider's account-level data retention policies. No research pages/results
are automatically saved to SQLite. Download research JSON to retain a result.

1. Enter a city and guest count in the research section.
2. For discovery, leave **Discover venues automatically** selected.
3. To read specific pages, paste up to five HTTP(S) URLs, one per line.
   Turn discovery off to research just these URLs.
4. Select **Research venues**, review sources and supporting excerpts, then
   download the JSON if needed. Supplied URLs take priority over search results.

Missing prices say **Quote required**. Availability and budget fit remain
unconfirmed/unknown. Capacity retains room/layout wording and requires human
confirmation. Source-backed means the text appeared on the page, not that the
venue's claims are independently verified. Search can return third-party
pages; inspect the source before relying on a fact.

### Research API

`POST /venues/research` accepts:

```json
{
  "city": "San Antonio, Texas",
  "guests": 40,
  "urls": ["https://venue.example/events"],
  "discover": false
}
```

Response: `query`, `candidates`, `errors`, `disclaimer`. Each candidate includes
nullable `details` (`name`, `address`, `capacity`, `contact`, `pricing`, plus an
`amenities` list). Each non-null fact has a verbatim `value` and `evidence`.
The candidate has `source_url`, `retrieved_at`, verification/availability/fit
labels and evidence rejection warnings. All candidate fields refer to that
source and retrieval time; null is not zero. Unsupported model claims are dropped.

- `422`: invalid request, over five URLs, or no source selected.
- `503`: missing keys or failed discovery with no supplied URLs to continue.
- `200`: completed research attempt, possibly with zero candidates and per-page
  errors. Partial results are retained; no synthetic fallback is invented.

Public HTML/plain text only, standard HTTP(S) ports, up to five unique URLs and
three redirects each. Reads are capped at 2 MB; extraction uses up to 24,000
readable characters per page. Private/local destinations are blocked, including
redirects; sockets pin validated IPs while retaining TLS hostname verification.
Robots permissions are checked before fetching pages. Inaccessible robots.txt,
unsupported crawl intervals, blocked sites, login/CAPTCHA pages without useful
venue details, PDFs and JavaScript-only pages may require another public URL.
There is no browser automation or bypass of access restrictions.

See [Brave API documentation](https://api-dashboard.search.brave.com/api-reference/web/search/get)
and [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

The API remains a local course MVP without authentication or rate limiting;
run it bound to `127.0.0.1`. The existing synthetic six-node demo does not need
these keys. Optional existing Pinecone live planning is separate from this feature.

Research requests have a 90-second wall-clock budget across search, fetching and
extraction. DNS lookups are additionally bounded to five seconds. A timed-out
external call can finish in a daemon worker; the number of workers is capped,
and the app does not automatically retry paid calls. Complex robots wildcard
or end-anchor rules are currently rejected conservatively rather than crawled.


### San Antonio, Texas scope

Venue research is limited to **San Antonio, Texas**. The research form uses a
fixed city; API requests default to that city and accept San Antonio / San
Antonio, TX aliases. Other cities return 422 before paid calls occur.
Discovery queries explicitly include Texas. Supplied URLs use the same scope:
a candidate must have a supported address naming San Antonio and TX/Texas.
Pages with missing or other-city addresses are excluded with an explanation.
This checks published address text, not geocoded city limits or actual travel
radius. Nearby cities are not included. An otherwise local venue page that
omits its city/state may need a different public address/details page.

The JSON example uses a fictional `venue.example` URL; replace it with the real
San Antonio venue website you want to research. Demo planning now defaults to
San Antonio and uses clearly synthetic local catalog entries. Their amounts
are demonstration fixtures, not researched San Antonio prices.

## Website planning agent

Open **http://127.0.0.1:8000/** and select **Run planning agent**. The website now
shows the six-node graph actually executing: Requirements, Budget, Vendor,
Schedule, Creative and Review. The activity feed is driven by streamed server
node/tool events, not simulated progress. Original Streamlit tools remain on
http://127.0.0.1:8501 and API documentation on /docs.

- **Live agent:** OpenAI chooses public search/page-read tools, observes their
  results and chooses subsequent actions. Keenable supplies search; existing
  robots, public-IP, size and deadline restrictions apply to reads. At most six
  tool calls over four model turns, followed by structured model ranking.
- **Catalog-only comparison:** runs the graph without model or web calls and
  explicitly labels recommendations as dated catalog comparisons.
- **Budget/capacity gates:** server checks every venue against children plus
  family, combines venue and decorator costs, includes the user-entered set-aside
  and rejects combinations whose known lower bounds exceed the allowance.
- **Review:** model may rank only server-eligible pair IDs. It receives bounded,
  source-attributed page excerpts, source failures and the party constraints.
  The server validates IDs and computes costs; model opinions cannot change
  capacity gates or invent prices/providers.
- **Honesty:** starting rates stay incomplete lower bounds. Failed reads and
  partial research appear persistently in the result. A page read never confirms
  the date, full quote, room layout, or Stitch package. Missing old source rates
  are invalidated in both recommendations and the website budget panel.
- **Use a recommendation:** selects that venue/decorator combination. New quotes,
  reserve or brief changes invalidate the old recommendation and cancel the
  active request. Run again to replan. Quote drafts are not sent automatically.

POST `/party/agent` accepts mode (live/catalog), city (San Antonio, Texas),
theme (Stitch), date, children, family, budget, reserve, and optional per-catalog-ID
quotes. Returns `application/x-ndjson` records: node/tool events, then a result or
error. Live mode requires OPENAI_API_KEY; catalog mode does not. Two active runs
are supported; excess requests return 429. Operations have an overall deadline;
timed-out provider work can finish in bounded daemon workers. No automatic model
retries, credentials in the browser, bookings, payments or messages. Tracing is
disabled in the launched server. Research results are not saved to SQLite.

The original six-node synthetic `/plans` workflow remains available separately.
