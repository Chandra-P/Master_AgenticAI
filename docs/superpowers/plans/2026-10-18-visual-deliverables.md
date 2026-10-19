# Visual Deliverables Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task, inline. User has asked to proceed without confirmation pauses.

**Goal:** Deliver a technical solution kit and a visual executive HTML dashboard while adding a restrained image background to the existing app.

**Architecture:** Extend the current validated report renderer; reuse its frozen source packet, arithmetic and citations. Embed pinned Bootstrap CSS and Chart.js JavaScript for offline portability, retaining SVG and tabular fallbacks. Generate the technical kit from real code, prompts and measured artifacts.

**Tech Stack:** Python, Streamlit 1.66, LangChain, LangGraph, ChromaDB, Bootstrap 5.3.8, Chart.js 4.5.1.

**Spec:** User attachment `835c115d-8a64-4bf8-9828-1ac40e4b903e/Pasted text.txt` plus the existing campaign design and factual-report constraints.

## Global constraints

- Direct mail: 60 days from mail/drop; display: 30 days from exposure.
- Preserve the three public workflows; technical explorer and evaluation remain development-only.
- Never fabricate experimental results, causal drivers, projected impact, ROI, or unmeasured time series.
- Maintain self-contained downloaded reports and source-validation gates.
- Keep existing hosted model/index defaults stable; document BGE as an explicit alternative requiring reindexing.

## Review focus

- HTML/JavaScript injection in campaign labels: escape embedded JSON and prose.
- JavaScript disabled or printing: preserve readable source-cited SVG charts and tables.
- Missing time-series/funding stages: render explicit availability cards, never interpolation.
- Incompatible historical cohorts: retain current exclusions and sample-size warnings.
- Altered source packet: existing fail-closed validation must still reject export.

### Task 1: Application appearance

- [x] Package the generated muted architecture background and cached Streamlit CSS.
- [x] Keep white content surfaces, dark sidebar and responsive background rules. Visual verification remains pending after user stopped browser control.
- [x] Run existing AppTest navigation/hosting checks.

### Task 2: Executive HTML dashboard

Files: `reporting/html_report.py`, new `reporting/dashboard.py`, packaged vendor assets, `tests/test_html_report.py`.

- [x] Add failing tests for offline Chart.js payloads, KPI variance/direction, missing-data disclosures, citation-safe audience/timeline views and script-safe JSON.
- [x] Vendor exact MIT-licensed frontend libraries; embed into reports with readable fallbacks.
- [x] Add chart callouts, evidence boundary/actions, recommendation cards and seven-part presentation storyline.
- [x] Preserve packet validation and verify all 20 campaigns render.

### Task 3: Technical kit and documentation

Files: new `deliverables.py`, `docs/technical_solution_kit.html`, `docs/campaign_performance_dashboard.html`, README and requirement audit.

- [x] Generate kit with architecture/workflow, component deep dives, exact code prompts, measured comparison tables/charts and reproducible commands.
- [x] Explicitly distinguish document retrieval metrics from actual RAGAS judgments and unavailable results.
- [x] Document model differences and unmet source-data requirements; build named outputs from the actual example packet.
- [x] Run tests and independent code review. Full suite: 105 passed, two known RAGAS deprecation warnings, 133.51 seconds.
- [ ] Inspect browser rendering: user stopped Computer Use with Escape; no further browser input attempted.
- [ ] Commit and push scoped files.

## Execution record

- Ruling: extend the existing implementation rather than create a second app. The attachment restates much of the shipped system; duplicating it would split report logic.
- Ruling: earlier explicit channel, factuality, and public-navigation choices remain binding. Paid-social examples and technical navigation in the generic attachment do not override those choices.
- Ruling: use measured artifacts only despite attachment wording “Generate realistic results”. Synthetic business inputs are labeled; evaluation numbers cannot be invented.
- Review: one P2 audience-table visibility issue found and fixed; no other important findings reported. Audience table now stays available after Chart.js initialization.
- Verification: 14 targeted navigation/report/hosting tests passed; all-20-campaign generation test passed; both requested HTML files built successfully from the validated saved RAG packet. No live model evaluations were started.
