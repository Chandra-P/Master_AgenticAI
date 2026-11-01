# Verification - October 31, 2026

## November 1 public planner foundation

### Confirmed Git destination and isolated release check

The user confirmed `Chandra-P/Master_AgenticAI`, main, for the CONVENE folder.
Prepared an isolated checkout to leave the parent workspace's protected Git
metadata and unrelated changes untouched. Only110 reviewed source files are
included; ignored credentials, databases, dependencies and runtime artifacts are
excluded. Credential-construction templates were reviewed separately from
literal-secret detection. Staged whitespace check passed.

Fresh verification against the isolated source copy: **134 passed in75.09s**
using `python -m pytest -q` with real isolated test-DB credentials supplied through
the child process environment, not copied into the checkout. Node suite:10passed.
`npm ci` and TypeScript/Vite build passed in that checkout. These are local
checks, not a claim that a root-level GitHub Actions workflow has run.

### Confirmed brief -> approved recommendations -> unsent inquiry preview

- Wired the current approved PostgreSQL directory into the six-node durable
  planner, category/capacity/location/price-floor matching, React option cards,
  saved shortlist and grouped inquiry previews. No runtime web search in this flow.
- Added `compare_catalog` as an owned confirmed-browser-session capability,
  separate from authenticated external research/communication. Confirmation now
  returns compare_catalog; Google sign-in/cross-device saving remains pending.
- Comparison caches bind event/brief version to the full published-directory
  revision. Approval changes invalidate reuse; stale shortlist versions are
  flagged. Full headcount is retained and missing costs are never zero.
- Approved-provider context now reaches conversational RAG after confirmation.
  Private evidence requires a matching current vendor version/approval; unlinked
  legacy evidence is quarantined. Source/history filtering, post-model rechecks
  and commit-time provider locks reject suspended/superseded excerpts.
- Independent review reproduced two freshness bypasses; added failing regressions,
  fixed both and reviewer found no remaining important issues in the fixes.
  Also verified partial unsupported model fields do not discard supported input;
  mixed contact-verification states cannot promote an unverified draft recipient.
- Final full result: **134 passed in 76.38s** via
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/catalog-final --tb=short`.
  Existing Node suite:10passed. React TypeScript/Vite build and Python compileall passed.
- Live HTTP/OpenAI workflow: detailed birthday brief (age10,30children,90parents,
  Dec6 afternoon,$2000,venue/decor,Stitch) -> one priority clarification -> review
  -> confirm -> six completed nodes ->3venue/2decor candidates. Published minimum
  floor was610, explicitly incomplete. Shortlisted South San/Navajo -> one shared
  office alternatives draft, empty recipient list, messages_sent=0. Follow-up
  capacity question returned a source-backed160-person maximum from approved_vendor
  context. Shortlist and preview were persisted/retrieved through the actual API.
- Legacy valid live requests to both web routes now return403 by default; old
  route regressions opt in explicitly. Legacy page defaults to catalog demo and
  links to the approved PostgreSQL planner. Both local health endpoints returned200.
- No provider calls/emails, bookings, purchases, payments or cloud resources.
  New option-card browser interactions were not visually/browser-automated here;
  acceptance evidence is build plus actual HTTP workflow, not a mobile UI claim.
- Setup/API/current limitations: [approved-catalog-planner.md](approved-catalog-planner.md).
- Parent Git remote rechecked:Chandra-P/Master_AgenticAI; no commit/push.

### PostgreSQL vendor approvals

- `/api/vendors` now reads PostgreSQL `vendor_records`, immutable `vendor_versions`
  and `vendor_approval_history`. Removed the generated Python approval function.
  Existing three venues/two decorators imported once; repeated import returned[]
  and did not overwrite, reapprove or recreate existing records.
- Stored version/hash, complete public details/contact evidence, creator label,
  reviewer provenance, effective approval date, recording time and reason. Initial
  approvals accurately identify the project owner's conversation approval, not
  a verified Google account. Authenticated admin UI remains future work.
- Draft changes leave the last approved version published. Stale-version approval
  conflicts, suspension hides the vendor and retains history, parent database
  connections cannot write or see drafts. No public administrative endpoint.
- Independent review prompted dedicated `convene_directory_admin` login/table
  ownership with SELECT-only website grants and role-based RLS. Tests forge the
  former admin flag and still fail to gain write/draft access. Credentials remain
  ignored/local. Production web deployment must not receive admin credentials.
- Full suite: **121 passed in 62.08s** via
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/vendor-roles-final --tb=short`.
  Frontend TypeScript/Vite build passed after clearing cached cards on refresh;
  existing Node suite:10passed. Explicit test-schema initialization and repeat
  admin import commands completed successfully.
- Live website and DB-backed directory returned200 with five version1 records and
  persistent approval IDs. Approval write endpoint absent. Directory refresh
  clears stale cards and fails closed if the approved list cannot be refreshed.
- [Administration and storage](vendor-directory-admin.md) documents exact tables,
  credentials boundary, import and draft/review/approve/suspend CLI commands.

### Approved directory and venue contacts

- Added sourced shared Bexar County Parks contact metadata to the three existing
  civic-center entries: 210-335-7275, office role/hours/timezone, official page,
  check date. Direct email remains null/not_verified, not guessed.
- Existing owner-approved inventory exposed via session-protected `/api/vendors`:
  three venues, two decorators, zero food providers. Opening the directory is
  catalog-only and does not call search/model services.
- React preview includes an expandable approved directory, category selector,
  Call/official-contact links and explicit unknown-contact/food states. Legacy
  venue detail dialogs also show the shared reservations contact.
- Full suite: **117 passed in 44.55s** via
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/vendor-contact-final --tb=short`.
  Node suite:10passed; JavaScript syntax check and TypeScript/Vite build passed.
- Restarted both local APIs. Live HTTP page and `/api/vendors` returned200;
  verified all three phone records and missing-email flags. Legacy `/party/catalog`
  also returned200 with the contact data. No phone calls or messages were sent.
- FDE design/current-versus-next scope: [approved-vendor-design.md](approved-vendor-design.md).
  The personalized catalog-to-RAG flow and disabling normal-flow legacy live
  search are still next implementation work, not claimed complete here.

### Conversational RAG release check

Final follow-up: explicit confirmation of an unchanged tentative value now clears
its tentative marker when supported by the current message. Added failing
regression before correction. Final full result: **115 passed in 27.60s**,
`.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/rag-tentative-final --tb=short`.
Reloaded the preview with this final correction.

- Added real PostgreSQL full-text retrieval before model generation, seeded with
  five passages of approved CONVENE planning guidance. This is lexical RAG, not
  vector search or an already-populated live venue corpus.
- Added owner/event/current-confirmed-version evidence indexing/retrieval. Stale
  private assistant history is excluded from the model; correction responses
  discard prior provider citations. Returned facts require current-message
  per-field quotes. Unchanged model echoes of the brief are ignored.
- Factual answers display only exact excerpts from retrieved sources. Unknown
  source IDs, unsupported claims under valid IDs and arbitrary small-talk claims
  are rejected. Source snapshots persist with assistant messages; React exposes
  expandable Knowledge used details and labels product guidance separately.
- Full result: **114 passed in 30.04s**, command
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/rag-release-final --tb=short`.
- Existing Node suite: **10 passed**. React TypeScript/Vite build: PASS.
- Restarted local preview. Real HTTP/OpenAI three-turn check: birthday daughter
  age10/30children/90parents -> venue and decorations -> budget-fit question,
  each HTTP200. Services saved, total stayed120, question did not mutate brief,
  source references resolved to planning-guests/scope/budget and all three
  sourced assistant turns reopened from PostgreSQL. Earlier runs exposed rejected
  echoes/document-vs-chunk reference mismatches; those were corrected with
  failing regressions before this successful check.
- Independent review found stale-evidence/history bypass and unsupported-prose
  grounding issues; regressions and fixes applied, reviewer rechecked them clean.
- Live provider ingestion, private upload UI, Google account save and Gmail/public
  hosting remain unfinished. Do not describe this as the complete public planner.
- Implementation/limits: [conversational-rag.md](conversational-rag.md).

Conversation correction: intake now classifies answer/small_talk/help/unclear
before applying facts. Non-answer turns and failed fact-evidence validation
produce a conversational reply without changing the brief or clearing confirmation.
The model has no research/messaging tools in this step. New assistant_message
is persisted and displayed even when the brief is ready for review.
Full suite: **102 passed in 22.79s**, command
`.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/conversation-green --tb=short`.
Frontend TypeScript/Vite build passed. Restarted preview; live HTTP/OpenAI
sequence `hi` -> `how ar you` -> `birthday` returned 200 each. Both social
turns preserved version1/empty facts; birthday became version2 and asked services.
This intake uses model extraction plus saved history, **not RAG**. General
event-scoped provider/document retrieval remains unconnected to the new chat.

Greeting correction: reproduced the screenshot's `hi` -> HTTP422. A live
synthetic service reproduction exposed a failed extraction-evidence check.
Simple greetings now use a deterministic warm reply, skip the model, persist
the conversation/idempotent receipt and preserve the brief/version. Messages
containing event facts still use extraction. Full regression result:
**99 passed in 17.15s**, `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/greeting-green --tb=short`.
Restarted the owned preview server to load the correction.

- New React/TypeScript intake preview: http://127.0.0.1:8001 (local computer only).
- Full command: `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/planner-check --tb=short`.
  Actual result: **95 passed in 14.05s**. Real, separate PostgreSQL test database;
  owner isolation and FORCE RLS exercised without a superuser/bypass role.
- Existing JavaScript suite: **10 passed**, `node --test tests/planner.test.mjs`.
- `npm run build`: TypeScript and Vite production build passed.
- New tests cover domain/policy constraints, stale brief versions, adaptive intake,
  unknown budget, family headcount, persisted retry receipts, cookie/CSRF checks,
  logout revocation, and PostgreSQL graph checkpoint restart/access isolation.
  Graph research tests use stubs; they do not establish live provider integration.
- Live HTTP preview check: page/health 200; session -> event -> real OpenAI
  extraction -> review_brief -> confirmed version -> sign_in all 200. Synthetic
  graduation inputs (venue, 40 guests, $2,000, December 6 afternoon) persisted
  correctly; three conversation turns reopened. This incurred OpenAI usage.
- `/plans` returns 404 on the new app. Legacy anonymous routes remain local only.
- Google sign-in, Gmail, public/mobile URL and hosted durability are **not yet
  implemented/verified**. No cloud resources or real emails created.
- Browser visual/interaction QA remains unavailable after the prior Computer Use
  URL-identification restriction. Build/HTTP checks do not establish mobile UI QA.
- Remote rechecked: `https://github.com/Chandra-P/Master_AgenticAI.git`. Intended
  CONVENE remote still unconfirmed; no commit/push or protected Git changes.
- Setup/API details: [public-planner-setup.md](public-planner-setup.md).

## November 2 demo readiness

- Installed all 78 declared dependencies in local `.venv`, using Python 3.12.15.
- Resolved versions captured in `requirements-lock.txt`.
- Acceptance suite: `14 passed in 1.48s`.
- Command: `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/run2`.
  Create `.pytest-tmp` first. The initial default run had 14 fixture setup errors
  because the sandbox could not access the system Pytest temporary directory.
  No application assertion failures remained with workspace-local temporary files.
- FastAPI launched on http://127.0.0.1:8000; `/health` returned `{"status":"ok"}`.
- Streamlit launched on http://127.0.0.1:8501; `/_stcore/health` returned `ok`.
- Streamlit AppTest exercised the actual UI against the running HTTP API:
  default Seattle brief -> six LangGraph nodes -> persisted SQLite plan ->
  retrieved identical plan -> Load saved plans rendered JSON. No UI errors or
  exceptions; one JSON download control rendered.
- Default demo: 40 guests, $5,000 budget, $1,780 estimated vendor total,
  `ready_for_human_review`. All vendor suggestions are synthetic.
- Both services launched with `CONVENE_MODE=demo`, `LANGSMITH_TRACING=false`
  and `LANGCHAIN_TRACING_V2=false`. No API credentials required.
- Live OpenAI, Pinecone and LangSmith: NOT VERIFIED; outside the demo checks.
- Browser rendering and actual file download: NOT VERIFIED; UI checks used
  Streamlit's headless AppTest framework.

## Git handoff

`git remote -v` resolves to `https://github.com/Chandra-P/Master_AgenticAI.git`
for fetch and push. This has not been established as the intended CONVENE
repository. No commit or push performed; protected `.git` was not changed.
Use the top-level `CONVENE/` folder for the verified environment and running apps;
the second copy under `Campaign-Intelligence-Hub/CONVENE/` was not modified.

## Repeat on Windows

From the top-level CONVENE folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
New-Item -ItemType Directory -Force .pytest-tmp | Out-Null
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/local-check
$env:CONVENE_MODE='demo'
$env:LANGSMITH_TRACING='false'
$env:LANGCHAIN_TRACING_V2='false'
.\.venv\Scripts\python.exe -m uvicorn convene.api:app --host 127.0.0.1 --port 8000
# In a second terminal, with the same environment settings:
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Stop existing servers before reusing these ports. Runtime logs, virtual
environment, local test temporary files, and SQLite data are ignored by Git.

### October 31 venue research implementation

- Added optional real venue research with automatic Brave discovery and supplied
  URLs, OpenAI structured extraction, source links, exact supporting excerpts,
  UTC retrieval times and JSON export. Existing synthetic plans stay separate.
- Added POST /venues/research and the Streamlit Research real venues section.
- Unit/API/UI suite after fixes: `49 passed in 4.12s` using
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/deadline-green`.
  Tests mock paid provider/network boundaries; they do not establish live model
  behavior or search account access.
- Independent review found robots wildcard bypass, malformed request-rate error,
  and incomplete deadlines. Reproduced each in failing tests, then fixed them.
  Complex wildcard/end-anchor robots rules now fail closed with an explicit
  unsupported-page error. Positive crawl rates are validated before use.
- DNS, search, page fetch and model extraction use one 90-second research
  deadline, with bounded daemon workers so stalled external calls cannot hold
  the HTTP request indefinitely. Timed-out provider work may finish in its
  worker; retries are disabled and workers are capped. No automatic retry of
  paid extraction occurs.
- Repeated public fetch smoke check after fixes: PASS on
  https://seattlecc.com/scc-campus/ ; 8,773 readable characters, robots checked,
  fetched 2026-10-31T16:40:22.527094+00:00. No paid service used in this check.
- Neither OPENAI_API_KEY nor BRAVE_SEARCH_API_KEY is configured. Live model
  extraction and automatic Brave discovery remain NOT VERIFIED.
- Compileall: PASS for convene, scripts, tests and streamlit_app.py.
- Current remote still Chandra-P/Master_AgenticAI; no commit/push or protected
  Git metadata changes performed.

### Running-service checks after restart

- FastAPI `/health`: PASS; Streamlit `/_stcore/health`: PASS.
- OpenAPI includes `/venues/research`: PASS.
- Live local HTTP research request without credentials returns 503 with
  actionable OPENAI_API_KEY configuration detail: PASS.
- Streamlit AppTest against the restarted API created a six-node synthetic plan,
  verified ready_for_human_review, retrieved identical SQLite data, and displayed
  the missing-key message from the research form without an exception: PASS.
- Synthetic default estimate remained $1,780. No paid requests were attempted.

Final acceptance run: `49 passed in 5.58s` using
`.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/final-venue-check`.
Final independent review: no remaining important issues in the three fixes.
Shared worker limits may return an explicit busy error under concurrent research;
this remains a local demonstration application.

### San Antonio scope update

- Research UI fixed to San Antonio, Texas; API defaults/canonicalizes that city
  and rejects other cities before any paid call.
- Search includes San Antonio, Texas. Real candidates require matching published
  address evidence naming San Antonio and TX/Texas; missing/outside addresses
  are excluded with per-page explanations. This is a text evidence check, not
  geographic boundary verification.
- Demo UI defaults to San Antonio, backed by two clearly synthetic fixtures.
- Regression suite: `56 passed in 4.54s` using
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/san-antonio-green`.
- Live paid search/extraction still not verified; credentials remain absent.

San Antonio final verification: `57 passed in 5.81s` using
`.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/san-antonio-address-final`.
Independent review found no important scope issues. Added a regression and fix
for local addresses formatted San Antonio,TX without a space after the comma.
Running API schema defaults to San Antonio, Texas and rejects Seattle with 422.
Streamlit's San Antonio demo produced a six-node, ready-for-human-review plan
and retrieved the identical saved SQLite record.

Release check after removing duplicate widget initialization warning: 57 passed in 5.23s; restarted API/UI health and outside-city rejection PASS.

### Live OpenAI and UI verification - October 31

- Reused the user's existing OpenAI key from another project's local secrets in
  Git-ignored CONVENE/.env. No credential values were displayed or committed.
- Automated suite: `57 passed in 3.05s` after extraction instruction changes,
  command `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/live-prompt-check`.
- Initial live attempts showed intermittent exact-evidence rejections:
  1902 Venue address confirmation failed once; Pavilion name evidence failed;
  San Fernando Cathedral crawl delay exceeded supported limits. These attempts
  were not successes and no unsupported venue claims were accepted.
- Model schema/instructions now explicitly request shortest verbatim excerpts,
  exact capitalization/punctuation and complete published addresses. GPT-4.1
  extraction uses temperature 0. Strict evidence validation is unchanged.
- Direct live research succeeded on https://1902venue.com/ with supported name,
  San Antonio TX address and public contact details. Missing costs/capacity
  remained unknown. Availability stayed unconfirmed.
- Running API initially inherited sandbox network restrictions. Restarted the
  localhost API with outbound network access; POST /venues/research returned
  HTTP 200, one candidate, no errors for the 1902 Venue public page.
- Final Streamlit AppTest used the real running API and paid OpenAI extraction:
  supplied URL -> public page -> model -> evidence checks -> displayed venue
  and address -> JSON download control: PASS. One candidate, no UI/page errors.
  Address returned: 1174 East Commerce Street, San Antonio, TX 78205.
- Automatic Brave search remains untested/unconfigured. Keenable is not yet
  integrated. Live URL extraction no longer depends on those search providers.
- These live checks used public venue data and incurred OpenAI usage. They do
  not establish a venue's actual availability, quotes or extraction reliability
  across other sites. No browser file download was performed.

### Party planning agent implementation

- Added actual LangGraph-driven /party/agent with six nodes, model-selected
  search/read tools, bounded adaptive tool loop, constrained model ranking and
  deterministic capacity/budget gates.
- Website streams actual node/tool events, exposes source successes/failures,
  recommendations, rejected options, source links, known lower-bound costs,
  missing quotes, and apply-combination actions. Brief/quote/reserve changes
  invalidate recommendations. No automatic messages or bookings.
- Regression suite: `69 passed in 5.25s` via
  `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp/agent-release`.
- Node budget/stream/reconciliation suite: 10 passed via
  `node --test tests/planner.test.mjs`. Node syntax and Python compileall passed.
- Independent review found all-failed research could look successful, and
  applying recommendations could restore invalidated prices. Added failing
  regressions then corrected persistent research status/warnings and price
  reconciliation. Reviewer found no further important issues in the fixes.
- Final ranking now receives bounded source-attributed page excerpts, not just
  read metadata. This supports evidence-informed tradeoffs but still requires
  human confirmation of vendor claims.
- First live test actually invoked model-selected read tools, but county robots
  crawl delays exceeded the original five-second support. This run was not a
  successful source verification. Added support for crawl delays up to twenty
  seconds within the total deadline and a regression for the county's ten-second
  interval; still fail closed for unsupported rules or insufficient time.
- New browser UI interaction not verified in this turn: Windows Computer Use
  previously stopped because it could not reliably identify the browser URL.
  Server/API/stream and JavaScript logic checks performed instead.

Final live agent test: PASS via actual POST /party/agent stream with live mode.
The model independently chose four read_page calls and read these public sources:
South San Civic Center, Belle of Balloons, Navajo Civic Center and Bewitchin
Balloons. All four reads completed while honoring crawl intervals. Six nodes
completed; research_status=sources_read. Structured Review returned three valid
catalog combinations, starting with South San + Belle at $610 in known base /
minimum costs. This is not an all-in quote, confirmed availability, or a complete
$2,000 party budget. No search tool was called in this run because catalog
sources were already supplied; Keenable tool execution is covered separately.
The streamed catalog-mode API also correctly returned needs_changes with no
recommendations for a $1,000 budget and $800 set-aside. Website HTML/JS endpoints
returned 200. No browser interaction verification claimed for the new controls.
