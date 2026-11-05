# Discovery, Notes, and typing suggestions implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development for independent tasks and final review. Preserve unrelated work. Do not commit in the integration checkout; the coordinator synchronizes scoped files and commits the deployment branch.

**Goal:** Show actionable individual places, save selected places into a shared draft itinerary, consistently ground assistant replies in saved Notes, and suggest optional chat continuations.

**Architecture:** Retain Next.js, FastAPI, Supabase, OpenAI, Pinecone, and Keenable. Reuse current authenticated plan editing and version checks. Keenable discovery will extract individual venues and source-backed image links from public page evidence, never turn an article into a restaurant or invent photos. Missing photos use an explicit empty state. No new paid account or billing is enabled.

**Tech Stack:** Existing TypeScript/React, Python/Pydantic/httpx, Playwright/pytest.

Ruling: User asked to fix everything and previously requested autonomous execution; proceed without design approval pauses. New provider purchases or billing remain outside authorization.

## Tasks
- [x] Notes: failing tests for ordinary chat receiving current saved documents before indexing; bounded direct Notes grounding plus optional historical RAG, stale/deleted source checks, no cross-plan data, preservation of verified citations.
- [x] Typing: local optional plan-aware next-word/short-continuation suggestions; Tab accept, Escape dismiss, mobile accept button, IME-safe Enter, never auto-send. No draft text sent externally. Test keyboard and privacy behavior.
- [x] Discovery: inspect actual provider outputs, extract individual place cards with sourced photo/website/address where available; add safe direct Maps links and persistent source metadata; save to selected plan/day/time with deduplication and revision validation. Article results never masquerade as venues. Tests for malformed/unsafe content, no photos, saving and persistence.
- [x] Run lint/typecheck/build, frontend and shared suites, backend pytest, public search/provider smoke without private data, desktop/mobile visual checks, and independent review.
- [x] Correct new multi-day date polls to offer full ranges; show the full working range and preserve original votes on legacy polls rather than silently reinterpreting them.
- [x] Make READY_TO_FINALIZE open a visible final review of dates, per-person budget, itinerary and remaining choices; route to itinerary from the review. Readiness does not imply bookings, unanimous agreement, or persisted finalization.
- [ ] Synchronize scoped source, scan credentials, commit/push existing authorized deployment branch, verify public rollout, document remaining provider coverage limitations.
