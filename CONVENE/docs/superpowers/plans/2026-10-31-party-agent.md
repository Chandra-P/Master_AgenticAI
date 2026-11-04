# Party Agent Implementation Plan

> Use superpowers:executing-plans inline; spec: ../specs/2026-10-31-party-agent-design.md.

Goal: Expose real model-directed research and constrained recommendations in the party website.
- [x] Write failing tests for six-node catalog mode, rejection/cost arithmetic,
  live missing-key error, tool-call execution and API activity stream.
- [x] Implement convene/party_agent.py with request validation, deterministic
  assessment and bounded OpenAI search/read tool loop plus structured ranking.
- [x] Add streamed /party/agent endpoint and accessible website action/activity,
  results, source state and apply combination. No fake progress steps.
- [x] Test actual API live tool calls, full Pytest/Node suite and source serving.
  Seek independent review, fix findings, update actual verification/docs.

Ruling: User's 'ok' accepts the concrete proposed agent behavior in previous
message; execute rather than reopen design questions. Work in existing CONVENE
subtree; protected .git remains untouched. No other-project changes.


Execution ledger: complete. 69 Python and 10 JavaScript tests passed. Live
stream exercised four model-selected public-page reads and valid model-ranked
combinations. Independent review fixes covered failure honesty and stale price
reconciliation. Source excerpts now feed model ranking. Ruling: four turns
instead of three allow both venue and professional decorator inspection while
keeping the six-call ceiling and overall deadline. No protected Git changes.
