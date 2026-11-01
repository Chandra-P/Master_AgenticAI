# Venue Web Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Discover real venues and extract sourced details from public URLs.
**Architecture:** A bounded public-page fetcher feeds structured OpenAI extraction; Brave discovery and supplied URLs share the same research service. FastAPI exposes the service and Streamlit presents research separately from demo estimates.
**Tech Stack:** Python 3.12, stdlib HTTP/HTML/robots, existing httpx/OpenAI/Pydantic, FastAPI, Streamlit.
**Spec:** docs/superpowers/specs/2026-10-31-venue-web-research-design.md

## Global constraints

Preserve six demo nodes and API-key-free demo. No bookings/payments. Tracing off by default. Maximum five URLs; only public HTTP(S) pages. Never invent missing venue facts. No commits until intended remote is confirmed. User approved real venue research, overriding synthetic-only guidance for this feature.

## Review focus

Private IPs and redirects must fail before contact; robots errors must fail closed; model quotes must match text and extracted values; supplied URLs must work without a search key; mixed success must retain successful results with explicit errors.

### Task 1: Public website fetcher
Files: convene/web_fetch.py, tests/test_web_fetch.py.
Interface: fetch_page(url: str) -> Page(url, text, retrieved_at).
- [x] Write failing tests for private targets/redirects, HTML cleanup, robots rejection, unsupported content and size bounds.
- [x] Run tests to prove feature missing; implement pinned-IP HTTP requests with TLS hostname checking, deadlines, limits, robots handling and readable HTML extraction.
- [x] Run tests green.

### Task 2: Evidence-backed research and API
Files: convene/venue_research.py, convene/api.py, tests/test_venue_research.py.
Interface: ResearchRequest(city, guests, preferences, urls, discover); research_venues(request) returns candidates, errors and disclaimer. POST /venues/research exposes it.
- [x] Write failing tests for required configuration, evidence rejection, null pricing, discovery URL deduplication, partial failures and API validation.
- [x] Implement Brave search, typed OpenAI output, exact evidence checks, nullable details, source metadata and explicit failures. Use existing SDK; do not add unnecessary dependencies.
- [x] Keep real research separate from synthetic estimates; optionally attach current research to exported UI proposal as a separate field, with unknown overall real-world budget fit.
- [x] Run tests green and existing acceptance suite.

### Task 3: UI, documentation and demo verification
Files: streamlit_app.py, tests/test_research_ui.py, .env.example, README.md, docs/verification.md, AGENTS.md.
- [x] Write failing Streamlit tests for URL/discovery submission and visible sources, errors, unknown pricing and JSON export using mocked external boundary.
- [x] Add research controls, clear paid-call notice, evidence display and session-only results.
- [x] Document keys, source limitations, API behavior and actual verification.
- [x] Run full suite and compile checks; restart only this project's servers and verify health and UI regression. Live paid extraction is verified only if credentials exist.
- [x] Request final independent code review; resolve important findings and rerun relevant checks.

## Execution ledger

Ruling: Work within the existing untracked CONVENE subtree. AGENTS.md prohibits altering protected .git, so git worktree scripts/commits cannot run. Existing unrelated workspace changes remain untouched.
Ruling: User's 'ok go' authorizes continuous implementation of the approved design; proceed inline without another approval round.

Task 1: complete - fetcher implemented, 13 initial fetch tests green; security regression tests added.
Task 2: complete - evidence-backed service and API; research fixtures and original acceptance suite green.
Task 3: implemented - UI, docs and server restart; final verification pending below.
Ruling: Keep web research as a separate action and export, rather than inserting unpriced real venues into the synthetic graph's budget calculation. The design permits optional plan attachment; this first version prioritizes honest costs and demo stability.
Review: corrected unsupported robots patterns by failing closed, invalid rates via FetchError, and operation deadlines via bounded external work. Failures reproduced before corrections.


Task 3: complete - services restarted, original UI/API/SQLite workflow verified, research setup errors verified, 49 passed in 5.58s on final suite. Final independent review reports no remaining important issues in the fixes. Live paid search/extraction remains unverified because credentials are absent; public website fetching was verified. No commit performed.
