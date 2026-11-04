# Party Website Implementation Plan

> For agentic workers: use superpowers:executing-plans inline.

Goal: Deliver the approved venue and professional decoration comparison website.
Spec: docs/superpowers/specs/2026-10-31-party-website-design.md.
Architecture: FastAPI serves static HTML/CSS/JS and an official-source catalog;
existing research endpoint remains available; add Keenable discovery.

- [ ] Test-first API catalog, root serving and safe source records. Implement
  convene/party_catalog.py and web/index.html, styles.css, app.js, planner.mjs.
- [ ] Test budget calculation (unknown quotes, exclusions, reserve, overspend),
  selection persistence and shortlist export using Node built-in test runner.
- [ ] Add real official-source venue and professional decoration cards, images,
  modal details, controls, quote-entry and responsive layout. No automatic calls.
- [ ] Test Keenable response mapping then implement in venue_research.py using
  existing httpx; retain Brave as explicitly selectable provider. Update docs.
- [ ] Run full Pytest/Node suite, restart network-enabled API, inspect desktop
  and mobile in browser, fix observed failures, obtain independent review.

Ruling: User's perfect/create instruction approves preceding written UI design;
proceed without another approval gate. Keep the new website integrated with the
local Python backend because a separate static hosted mockup cannot call the
user's localhost backend or safely use its local credentials. No hosting scope
or account changes. No parent Git worktree mutation because protected .git.
