# CONVENE venue web research design

Date: October 31, 2026. Target: November 2 demo.

## Intent and scope

Add real venue research to CONVENE: discover venues by city and guest count,
extract details from user-supplied venue URLs, or combine both. User selected
search plus website extraction over model-only web research.

User's request authorizes real venue data, superseding AGENTS.md's synthetic-only
restriction for this research feature. Keep existing synthetic demo operational.
No bookings, purchases, payments, vendor contact, or availability guarantees.

## Approaches considered

1. Search API plus bounded website extraction (selected): explicit sources,
   reusable extraction for supplied URLs, testable provider boundaries.
2. Model web research directly: quicker initial integration, less control over
   retrieval and reproducibility. Not selected.

## Proposed implementation decisions

Keep Python/FastAPI/Streamlit/LangGraph and the six existing nodes. Add an
explicit venue research action in Streamlit and POST /venues/research with city,
guest count, optional preferences and up to five URLs. An explicit discovery
flag controls whether to search in addition to reading supplied URLs.

Proposed default provider: Brave Search API for discovery, configured through
BRAVE_SEARCH_API_KEY; OpenAI structured extraction of fetched page text through
OPENAI_API_KEY. These are proposed implementation choices, not user-selected
providers. Supplied URLs skip the search provider. No Pinecone requirement for
web research. Missing credentials return actionable errors, never fake results.

Research returns candidates separately from the synthetic planning catalog.
The Vendor node may attach researched venue candidates to a plan when explicitly
requested; synthetic estimates must remain clearly separated and must not be
presented as a real-world total. Existing /plans requests retain their behavior.
Real venue candidates do not inherit synthetic prices or catering records.

## Evidence and data handling

Extract name, location/address, capacity with room/layout context, amenities,
public business contact details and published pricing with currency, unit and
conditions. Preserve missing fields as null, not zero. Each extracted claim
must have an exact supporting text excerpt, source URL and UTC retrieval time;
reject claims without matching evidence in the fetched text. Label web-published
claims as unverified by CONVENE. Do not assert dates are available.

Budget fit is unknown without comparable published costs; capacity fit is
unknown when capacity or applicable layout is missing. Show candidate matches,
missing information, failures and source links, plus JSON export. Research is
not a booking or a complete budget estimate. Do not silently substitute demo
venues when search/extraction fails.

Fetch only public HTTP(S) pages with bounded response sizes, deadlines and
candidate counts. Validate DNS/IP destinations including redirects; deny local,
private, link-local and metadata destinations. Respect robots restrictions;
identify the client. Do not bypass login, CAPTCHA, paywalls or blocked pages.
For the first version, unsupported JavaScript-only/PDF pages produce explicit
per-page errors. Treat webpage instructions as untrusted data. Never send keys
or full personal event briefs to websites/search; search by city and venue needs.
Tracing remains disabled by default. Model and search calls may incur costs.

No automatic persistence of fetched pages or research; retain results in current
UI session and optional downloaded JSON. Existing plan persistence stays local.

## Verification and handoff

Use mocked provider/HTTP fixtures to verify evidence checks, absent pricing,
partial failures, bad URLs, redirects and existing demo behavior. Exercise
Streamlit research controls and API output. Run full Pytest acceptance suite
using workspace-local temporary storage. Run a live public-page smoke test if
credentials/network are available; otherwise explicitly report it unverified.
Update setup, environment example, API docs and verification notes. Do not
commit until the intended remote is confirmed; never alter protected .git.

## Left to implementation

Module boundaries, bounded retry details, conservative extraction token limits,
exact schema naming and presentation arrangement. Review official provider
and installed library documentation before using their APIs. Prioritize a
working URL extraction path and then automatic discovery for the demo.

## Approved follow-up: San Antonio scope

User requested San Antonio, Texas. Research is now limited to that city, with
canonical API aliases and a fixed UI city. Candidates require source-backed
address text naming San Antonio and TX/Texas; missing/outside addresses are
reported, not accepted. This is not geocoded boundary validation. Demo defaults
to San Antonio with clearly synthetic fixtures. Full suite: 57 passed in 5.81s.
