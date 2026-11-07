# Guided AI Planning and Layout Polish Implementation Plan

> **For agentic workers:** Use executing-plans or subagent-driven-development to implement the checked tasks, preserving existing collaboration and source boundaries.

**Goal:** Make the AI contribution and the next user action visible, reduce repeated manual input, and fix desktop/mobile layout friction.

**Architecture:** Keep Next.js/FastAPI, current styling, current plan generation and explicit human consent. The model proposes starter interests with a short rationale; the draft review explains what was extracted and highlights missing details. A single explicit action searches a balanced/model-proposed set of interests, with editable suggestions and source receipts. No automatic votes, bookings or assumed group preferences.

**Tech stack:** Existing React/TypeScript/CSS, Pydantic, OpenAI structured generation and existing place/event provider. No dependencies or migration.

- [x] Audit existing screens and add narrowly scoped responsive layout fixes without replacing Srishti's design.
- [x] Add backward-compatible model-proposed interests/rationale to plan drafts, validate and test output.
- [x] Reorganize plan generation around the idea first, explain the AI draft, highlight missing information, and offer one-click sourced suggestions without requiring every interest manually.
- [x] Add a visible guided journey/next action to saved plans, retaining existing options, comments and consent rules.
- [x] Verify layout, source handoffs and collaboration with meaningful desktop/mobile regression tests; run lint, types, build and required suites.
- [x] Review, preserve teammate changes, push and verify live release.

User direction: audit and fix similar layout issues and make AI assistance intuitive; prior instructions authorize autonomous implementation, testing and publication. Existing account data is retained. Live source availability remains best effort and clearly labeled.
