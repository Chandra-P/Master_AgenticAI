# KidSpark Fair Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Execution method: native, preserved from the existing project workflow.

**Goal:** Make practice varied, rankings fair, and personal improvement visible while preserving saved results.

**Architecture:** Retain Streamlit views and the existing SQLite schema. Add a versioned authored question bank and objective-based round selection; validate stored answers by version and question identity. Derive badges and improvement from saved attempts rather than new tables.

**Tech Stack:** Python, Streamlit, SQLite, pandas, Plotly; no new dependencies.

**Spec:** [Approved design](../specs/2026-10-11-kidspark-fair-practice-design.md)

## Global constraints

- Five decisions, three choices, 20 points per correct answer; hints and speed do not affect scores.
- Three variants per objective: 90 questions across three challenges and two levels.
- Keep version-1 answer mappings, version-1 histories, and identical save retries.
- New rounds use version 2; introductory objective first, remaining four shuffled.
- Overall ranking requires all three challenges at the selected level; shared ranks for equal totals.
- Leaderboard viewing defaults off and is not a publication opt-out.
- No accounts, new services, secrets access, destructive database migration, or publishing.
- Local video/submission guides remain ignored. Verification uses temporary databases.

## Review focus

1. A valid version-1 save retry must remain identical and must not add a row (Task 2).
2. Two questions from one objective must be rejected even if IDs differ (Task 2).
3. A completed zero-score round earns its completion badge (Task 4).
4. A lower latest score must not erase best score or produce mastery claims (Tasks 3–4).
5. Equal completion timestamps require deterministic first/latest ordering (Task 3).

## Task 1: Versioned content and round selection

**Files:** `src/kidspark/challenges.py`, new `src/kidspark/question_variants.py`, `src/kidspark/game.py`; `tests/test_challenges.py`, `tests/test_game.py`, and UI helpers in `tests/test_learning_app.py`.

**Interfaces:** Keep `get_questions(challenge: str, level: str) -> tuple[Question, ...]` as the canonical five-question compatibility accessor. Add `question_bank(challenge: str, level: str, version: str) -> tuple[Question, ...]` and `select_questions(challenge: str, level: str, seed: str) -> tuple[Question, ...]`. Add an `objective: str` property to Question, derived from explicit bank metadata. `start_round` retains its public signature and seeds selection with its new UUID.

- [x] Write tests: banks contain 30 historical/90 current questions; each current objective has three unique variants; prompts <=18 words and fact panels <=55 words; six rounds each select five distinct objectives; same seed reproduces questions; multiple seeds expose all variants and varied order while keeping the starter first.
- [x] Run those tests and confirm failures against the current static bank.
- [x] Archive the existing bank, author 60 additional comparable variants with reviewed explanations, and implement the accessors and selection. Retain original choice indices in the archive. Keep authored option order fixed.
- [x] Change UI test helpers to answer `app.session_state['round'].questions`, not a separately fetched static round. Make mixed-score skill tests use explicit fixtures so randomness cannot make assertions flaky.
- [x] Run content/game tests and inspect every variant's calculations, clues, and difficulty rubric.

## Task 2: Version-aware persistence

**Files:** `src/kidspark/storage.py`; `tests/test_storage.py` and a historical-answer fixture in `tests/fixtures/`.

**Interfaces:** Consume `question_bank` from Task 1. Keep `save_attempt`, `load_attempts`, result fields, and SQLite schema unchanged. `_validate(result: dict) -> None` resolves versioned question IDs and verifies one per objective for version 2; version 1 retains its original fixed order validation.

- [x] Write failing tests for shuffled version-2 saves/reopens, duplicate IDs/objectives, foreign challenge/level IDs, incorrect answer/skill, unsupported version, and a historical version-1 save/retry/reopen fixture.
- [x] Run storage tests to confirm the missing behavior fails.
- [x] Implement version-aware validation without rewriting old records; keep parameterized transactions, idempotency, and all current totals/time/identity guards.
- [x] Run storage/game tests; verify existing version-1 results and new varied rounds coexist in one temporary database.

## Task 3: Fair rankings and personal comparisons

**Files:** `src/kidspark/progress.py`; `tests/test_progress.py`.

**Interfaces:** Keep `challenge_leaderboard(best_scores: list[dict], challenge: str | None = None) -> pd.DataFrame`; overall mode filters to three distinct supported challenges. Add `challenge_progress(attempts: list[dict], level: str) -> list[dict]`, one row per fixed challenge with `challenge`, `rounds`, `first`, `latest`, `best`, and `change`; unplayed score fields are None, change is None until two rounds. Sort by parsed UTC completion timestamp and attempt ID.

- [x] Write failing tests: one/two-challenge profiles have no overall rank; all-three profiles rank by best totals; individual rankings include partial participants; equal totals share ranks; duplicate summaries do not inflate points.
- [x] Add first/latest/best/change tests for unsorted histories, lower latest scores, timestamp ties, zero scores, empty histories, and school-level separation.
- [x] Run progress tests, then implement the eligibility and ordered comparison functions.
- [x] Rerun progress tests and confirm independent recommendations and weighted accuracy still work.

## Task 4: Learning-first dashboard and complete flow

**Files:** `src/kidspark/ui/progress.py`, `src/kidspark/ui/app.py`, `src/kidspark/ui/play.py`; `tests/test_learning_app.py`.

**Interfaces:** Consume `challenge_progress` and existing saved attempts. Add a `show_leaderboard` checkbox defaulting false; call `render_leaderboard` only when enabled. Existing render signatures remain unchanged.

- [x] Write failing AppTest checks for no default leaderboard query/render, checkbox enable/filter, eligibility copy, level separation, completion badges including zero scores, explorer badge after three challenges, first/latest/best display, and persistence after a fresh session.
- [x] Implement per-challenge score comparisons and badges, optional ranking view with clear publication notice, and encouraging eligibility/empty states. Keep all-history summaries distinct from selected-level comparisons.
- [x] Add concise practice copy about variant questions, equal scoring, free hints, and no time pressure. Avoid negative-rank or mastery messaging.
- [x] Run the full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`; require zero failures and app exceptions across all six round combinations.

## Task 5: Documentation, demonstration, and review

**Files:** `README.md`, `docs/architecture.md`, `docs/learning-content.md`, `docs/future-enhancements.md`, `docs/verification.md`; ignored local guides.

- [x] Update the bank/versioning architecture, eligibility examples, viewing/publication distinction, difficulty rubric, limits, and video walkthrough. Remove superseded static-question and partial-participation claims.
- [x] Execute demo rounds for all three challenges in an isolated database; verify eligible/partial profiles, improvement, and level filters. Record actual results and checks, not hypothetical outcomes.
- [x] Start the local app and check its health endpoint. Perform browser visual review if available; accurately report any tooling limitation.
- [x] Use requesting-code-review for one independent final read-only review; resolve critical/important findings and rerun affected checks.
- [x] Report verified test counts, changes, and remaining account/student-evaluation limits. No Git commit is planned because this workspace is not a repository.

## Plan self-review

All approved design sections map to tasks above. Interfaces are explicit;
storage needs no schema migration, and ranking needs no new database query.
Review-focus edge cases have assigned tests. Native execution is retained.
