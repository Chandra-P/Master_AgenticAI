# Agent design

Agents are bounded capabilities in an explicit Python workflow, not independent unconstrained personas. The public trace contains node names, tool names, status, latency, sources, and calculation outputs. It never includes private chain-of-thought.

| Node | Allowed work | Failure behavior |
|---|---|---|
| Orchestrator | Choose sql/rag/memory/affordability/subscription_scenario/goal_comparison/scenario/tax/clarification | Unsupported or unidentified referent → clarification |
| SQL analytics | Approved parameterized Analytics functions | Missing/failed required evidence → no invented balances |
| Document RAG | Owned, eligible, non-quarantined evidence | Missing/conflicting offer terms → abstention |
| Subscription | Known billing schedule and recurrence evidence | No claim of unused plans; selected IDs required for cancellation |
| Goal/memory | Active goals and preferences | Cannot silently replace constraints |
| Scenario | Decimal functions, validated composed inputs | Missing APR/invalid IDs or input → specific error |
| Critic/validator | Cash/cash-flow and earmark identities, independent goal timelines, inclusive reserve boundary, amortization residual, semantic-field/unit provenance, summary monetary/rate/term claims | Failed validation blocks recommendations |
| Advisor/synthesis | Deterministic templates populated from validated facts | Partial ownership costs remain a visible limitation |

OpenAI mode uses a strict tool-calling schema, `select_route(route: enum)`. It cannot create new tools or pass arbitrary SQL. The same graph executes after route selection. Deterministic fallback uses broad intent patterns and explicit periods, not a lookup of golden question strings. Clarification safety gates cannot be overridden by the model.

Each financial fact includes label, value, unit, source reference, and semantic output path. The validator checks that exact allowed field or labeled document extraction; it cannot validate cash using a record count elsewhere in the result. Summary dollar/rate/term numbers must appear among validated facts. This is deliberately stronger than checking whether any number appears somewhere in tool output, but it is not a general semantic proof system.

`agent_runs`, `tool_calls`, and `citations` persist question, route, node sequence, sanitized inputs/outputs, validation, errors, answer, and latency. Local traces contain synthetic financial facts; basic redaction removes recognizable API keys, emails, and account-like long numbers. Optional LangSmith sends only minimized route/tool/status metadata.

The app has no cross-session conversational referent memory. An isolated “Can I afford it?” must ask for the item. Critical memory is stored in structured preferences rather than chat retrieval. Clickable evidence and calculation drawers provide the follow-up explanation without rerunning unnecessary tools.

Failed tools retain their names and error categories in the trace. If audit storage is unavailable, the API still returns a transparent blocked answer and reports that the trace could not be persisted.

Tax & Payroll nodes read only explicitly confirmed facts, use cached official2026 rules, and separate liability, withholding, payroll tax and net cash cost. Tax Scenario connects the modeled net payroll change and a tax reserve to the goal engine. Copilot requires one named worker and one unambiguous change type; combined changes use the structured form. Payroll documents stay local. A passed next-pay date blocks new strategy forecasts until a current stub is reviewed.

## Optional model council

After validation/synthesis, `council.review_council` invokes three independent bounded reviews for decision workflows. `off` skips; `demo` uses labeled local policy simulation; `openai` calls three configured models with schema-only responses. Code reconciles all votes, applying a deterministic veto and preserving every original fact/calculation. Any caution/block means held; any unavailable vote means incomplete. Failed reviews never receive invented replacement votes. A warning precedes the original deterministic analysis when review is held/incomplete. Council does not update goals/memory or authorize financial actions. The result, latency and event are stored before tracing/audit persistence. Golden runs use `use_model=False` and therefore explicitly disable councils. See MODEL_COUNCIL.md.
