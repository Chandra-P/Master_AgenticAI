# Connected planning journey implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development or executing-plans, with tests and a final review.

**Goal:** Remove dead ends between group needs, researched or manually added options, human decisions and the final itinerary.

**Architecture:** Preserve Next.js/FastAPI, existing theme, versioned decisions, authorization and JSON persistence. Four main tabs (Overview, Decisions, Chat, Itinerary) host contextual tools. A read-only research endpoint retrieves authorized current evidence and bounded external place results with factual execution receipts. Structured decision options retain website, estimates and notes; confirmed outcomes are shown in final itinerary review without pretending a booking.

**Approved scope:** User approved visible RAG/search, simplified navigation and connected lodging/other-option workflows, then instructed implementation across the journey. Later instructions add a saved four-friend demonstration and interest-led city/event suggestions. Local verification uses synthetic fixtures; separately authorized live checks use configured providers and the explicitly requested account demo. No new dependency or migration is needed.

**Alternatives:** Merely exposing traces leaves disconnected tools; replacing the existing app loses working collaboration. Extend the existing flows and keep legacy URLs accessible through contextual panels.

## Constraints and review focus
- Preserve teammate Discover and Groups behavior and all existing plan data.
- Keep current colors, spacing, typography and mobile accessibility.
- Actual execution receipts only; never fabricated progress or model reasoning.
- Read-only research cannot vote, finalize or book. Only owners edit decision options; members respond/comment.
- Options retain source links and unverified estimates. Decision changes invalidate ballots/finalization. Confirmed choices remain distinct from booked items.
- Recheck membership/revision after external calls; reject stale/cross-plan source references and account switches.
- Legacy tool links remain usable without becoming additional primary tabs.

## Tasks
- [x] Backend research: add bounded authorized retrieval/search endpoint and structured option details to versioned decisions; tests for source validity, partial failures, stale reads, ownership and legacy strings.
- [x] Navigation: four main tabs, contextual notes/research/legacy polls/demo bookings; Overview directs users to specific working actions.
- [x] Options: accessible per-decision add/search/compare flow with name, link, estimate, notes; sources and retrieval/tool receipts visible; explicit save and version-safe update.
- [x] Itinerary: show current confirmed outcomes and booking/verification next steps, not just manually added activities.
- [x] Browser regressions: lodging manual/search option, source inspection, vote/comment/finalize and mobile navigation; adapt legacy tests to contextual tools.
- [x] Verification: lint/types/build, backend/frontend/shared suites, independent review; document scope and evidence. Push/deployment follows established authorized release process only after checks pass.
