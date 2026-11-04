# Modern React UI refresh

Use the existing React19/Next.js15/TypeScript app. Preserve finance, payroll, tax, scenario, evidence, and evaluation behavior.

Design: navy navigation, neutral content canvas, white panels, teal primary actions, violet chart secondary, clearer typography, accessible dark mode, responsive stacked layouts. No new service or component framework is needed.

- [x] Shared navigation metadata and an accessible command palette: searchable pages/questions, Ctrl/Cmd+K, arrows/Enter, Escape, focus trap/restore, honest empty states. Add interaction tests before implementation.
- [x] Refresh dashboard hierarchy: sourced KPIs, income/spending chart, decision workspace, live-record goal progress, dynamic spending insights, tax-planning shortcut. Remove hardcoded loan-price and emergency figures from the decorative hero. Support missing goals.
- [x] Apply the visual system consistently across tax review, transactions, documents, scenarios, Copilot, evaluation, settings, desktop and mobile. Preserve existing labels and tested workflows where practical.
- [x] Run frontend lint/type tests/build and original backend/golden regressions; update browser test selectors and archive. Browser execution remains conditional on sandbox socket access; do not invent screenshots or claim unrun visual checks.

Assumptions: “React JS” means the React ecosystem; retain TypeScript for correctness. Existing light/dark support remains. Search navigates local pages and suggested questions, not unimplemented global financial-data search. Existing demo-source limitations remain visible.

Review follow-up: missing goals made the dashboard API fail before the empty UI could render. Added nullable projections, an explicit unavailable reason, and API/component regressions. No financial formula changes. See UI_RELEASE_REPORT.md and artifacts/ui-verification.log for executed results.
