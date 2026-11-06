# Reliable local typing suggestions and chat organization

> **For agentic workers:** Use superpowers:subagent-driven-development for isolated engine and composer tasks, followed by independent review. Work in the existing integration checkout; coordinator publishes scoped changes.

**Goal:** Ordinary planning drafts receive useful suggestions, with honest limits and predictable keyboard behavior; chat code becomes easier to maintain.

**Root cause to verify:** The current engine only recognizes narrow phrase prefixes and observed one/two-word transitions. Mention prefixes and incomplete first words often produce no result. Suggestions are shown independently of caret position, so mouse acceptance may append at the wrong position.

**Architecture:** Keep immediate on-device matching and add the user-requested OpenAI continuation in connected mode after a 750ms pause. A dedicated authenticated endpoint checks membership/revision before and after generation. Send only the bounded draft, plan facts, and four short human messages; no documents, RAG, tools or state writes. Use the existing OpenAI key and configured model, a five-second timeout, small output limit and bounded actor/concurrency limits. Extract chat rendering/composer from workspace into focused modules; remove only extraction leftovers. Preserve identity resets, IME, Tab/Escape, explicit acceptance, send and cancellation behavior. Abort and discard stale work on edits and context changes.

**Constraints:** No new keys, cross-plan context, automatic message sending, or feature removal. UI must disclose when enabled connected suggestions send drafts to OpenAI; demo remains local. Preserve existing engine cases and demo privacy tests. Model errors fall back to local suggestions honestly. No drafts are stored as messages or indexed.

## Tasks
- [x] Reproduce engine gaps; add failing tests; improve phrase/partial matching with bounds and isolation.
- [x] Extract Chat module; handle caret/composition/dismissal; add focused interaction regressions; remove unused imports.
- [x] Add bounded authenticated model continuation endpoint, provider, debounced cancellable frontend hook and model-specific tests.
- [x] Document actual behavior, limitations, contributor code map and verification commands.
- [x] Independent review, full lint/types/build/backend/frontend/shared checks, desktop/mobile screenshots.
- [ ] Sync, secret scan, commit/push and verify rollout.
