# Modern React UI refresh

FinPilot retains React 19, Next.js 15 and TypeScript. The refreshed interface uses navy navigation, teal actions, a neutral canvas, clearer financial cards and responsive light/dark layouts. No financial formulas, tax rules or database migrations changed. The dashboard API now returns an explicit unavailable projection when required data is missing, preserving the rest of the dashboard.

## Changes

- Shared navigation and accessible page/question search: Ctrl/Cmd+K, arrow keys, Enter, Escape, focus trap/restore and empty results.
- Dashboard uses recorded balances, reserve preferences, goal allocation, cash-flow history and spending anomalies. Decorative hardcoded loan-price and reserve figures were removed.
- Consistent visual treatment for finance, documents, Copilot, scenarios, Texas Tax Planning and Evaluation Lab.
- Empty-goal API/UI handling added so missing projection data does not hide available balances.
- Repeated suggested-question delivery fixed, with a failing-before/passing-after regression test.
- Actual React dashboard rendered into a clearly labeled, inactive static preview. Open `artifacts/ui-preview/index.html` or `dark.html` locally. This is not a browser screenshot or a substitute for running the application.

## Verification

Run `bash scripts/verify.sh` for Ruff lint/format, backend tests, isolated deterministic golden evaluations, frontend lint/typecheck/tests and Next production build. Ruff lint/format, ESLint, TypeScript checking and the Next.js production build all passed.

Executed regression results: **75 backend tests passed, 17 frontend tests passed, and 59/59 deterministic golden evaluations passed**. Golden-set SQL, scenario, tax, emergency-detection, routing, retrieval and citation metrics were 100%; forbidden-tool rate 0%, unsupported-claim count 0, prompt-injection tests passed. These metrics describe the isolated fixtures only.

Recorded output: `artifacts/ui-verification.log`; evaluation results: `artifacts/golden.json`.

Static-preview generation: `node scripts/generate_ui_preview.cjs` after `cd frontend && npm ci`. The script renders the actual components against `artifacts/ui-preview-data.json`, a synthetic fixture; the chart receives a fixed viewport for server rendering. Financial results still come from deterministic backend fixture outputs.

Live browser checks remain unverified: this environment blocked localhost socket binding and Chromium socket creation in prior attempts. Responsive and dark layouts have source-level review and component tests, but still need real-browser visual review on a laptop. Docker and live OpenAI/LangSmith integration remain unverified here.
