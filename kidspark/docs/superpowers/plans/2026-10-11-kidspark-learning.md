# KidSpark Learning Implementation Plan

**Current refinement:** The approved fair-practice design and plan supersede
static questions, partial-participation overall ranking, and always-visible
leaderboard requirements in this historical document. See
[the fair-practice design](../specs/2026-10-11-kidspark-fair-practice-design.md).

**Scope update:** The user requested removal of the sample/imported-score dashboard.
The application now displays only played challenge results. Earlier CSV-view
requirements below are superseded; offline CSV utilities and tests remain.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build engaging five-decision learning rounds with durable student results and an assignment-ready Python project.

**Architecture:** Keep Streamlit as the interface, separate pure game and progress logic into a `src/kidspark` package, and persist completed attempts in SQLite. Reuse the existing dashboard and validated CSV calculations in a separate imported-scores view.

**Tech Stack:** Python 3.10+, Streamlit, pandas, Plotly, sqlite3, unittest, Streamlit AppTest.

**Spec:** [Approved design](../specs/2026-10-11-kidspark-learning-design.md).

## Global constraints

- Five decisions per round; two school levels; three challenges; thirty authored decisions.
- Three concise choices, one correct answer, and a useful hint for each decision.
- Each correct decision earns 20 points: score is 0â€“100.
- Using a hint does not reduce points. No timed scoring, countdown, or speed ranking is used.
- Require 1â€“32 characters after trimming for nicknames; NFKC, collapsed whitespace, casefold for identity.
- Store completion timestamps in UTC and duration in elapsed seconds.
- Completed attempts persist; unfinished rounds remain in session state only.
- `/docs/submission-guide.md` and `/docs/video-guide.md` remain Git-ignored local files.
- No secrets or SSH keys will be read or committed.
- Do not initialize Git or make commits in this currently non-Git folder. Use file-level verification checkpoints instead.
- Keep runtime dependencies limited to the existing three packages plus the standard library.

## Review focus

- Nickname changes during feedback or completion: never save the previous round under the new nickname (Tasks 2 and 5).
- An unavailable database during completion: retain the frozen result and retry without duplicate inserts (Tasks 3 and 5).
- Old answer widgets after a new round: fresh attempt keys prevent stale selections or duplicate scoring (Task 5).
- Missing or invalid imported CSV: only the imported view fails; gameplay and history remain available (Task 6).
- Out-of-order or repeated actions: reject skipped questions, duplicate answers, and incomplete saves (Tasks 2 and 3).

## File map

- `app.py`: thin Streamlit launcher.
- `pyproject.toml`, `requirements.txt`: editable package install and dependency metadata.
- `src/kidspark/config.py`: application data paths and database override.
- `src/kidspark/challenges.py`: immutable, versioned question data.
- `src/kidspark/game.py`: nickname identity and round state transitions.
- `src/kidspark/storage.py`: SQLite attempt persistence and filtered history.
- `src/kidspark/progress.py`: saved-result aggregation and recommendations.
- `src/kidspark/metrics.py`: existing CSV functions moved without behavioral changes.
- `src/kidspark/ui/{app,play,progress,imported}.py`: Streamlit views.
- `tests/test_{challenges,game,storage,progress,metrics,app}.py`: corresponding checks.
- `docs/{architecture,learning-content,future-enhancements}.md`, `README.md`: public documentation.
- `docs/{submission-guide,video-guide}.md`: local assignment preparation.

## Task 1: Installable package and reviewed learning content

**Files:** Create `pyproject.toml`, `src/kidspark/__init__.py`, `src/kidspark/config.py`, `src/kidspark/challenges.py`, `tests/test_challenges.py`; modify `requirements.txt` and `.gitignore`.

**Interfaces:** `Question` frozen dataclass with `id`, `prompt`, `choices: tuple[str, ...]`, `correct_index: int`, `skill`, `hint`, and `explanation`. `get_questions(challenge: str, level: str) -> tuple[Question, ...]`; `CHALLENGES`, `LEVELS`, and `CONTENT_VERSION` constants. `data_directory() -> Path`; `database_path() -> Path` reads only `KIDSPARK_DB_PATH`.

- [x] Write `test_all_rounds_have_five_valid_questions`: assert six combinations, five decisions per combination, three unique choices, valid correct index, unique IDs, nonempty prompts/hints/explanations.
- [x] Run `python -m unittest discover -s tests -p test_challenges.py -v`; expect missing-package/content failure before implementation.
- [x] Add setuptools package metadata, existing dependency ranges, `requirements.txt` containing `-e .`, and the content/config interfaces above. Resolve data relative to the project, not process working directory. Ignore SQLite files/journals, caches, environments, and the existing local-only guides.
- [x] Author the thirty decisions from the approved content table, using connected school-outing, friend-message, and class-celebration stories. Start each round with a confidence-building question; each prompt must remain independently solvable. Review arithmetic manually against explanations, including discount order and tax assumptions.
- [x] Install with `python -m pip install -e .` and run the content tests; require all tests passing and imports resolving to this checkout. Read the installed Streamlit references using the skill discovery script before UI work; preserve minimum-version compatibility or explicitly justify an updated minimum.

## Task 2: Pure game rules and safe round transitions

**Files:** Create `src/kidspark/game.py`, `tests/test_game.py`.

**Consumes:** Task 1 `Question`, `get_questions`, `CONTENT_VERSION`.

**Produces:** `normalize_nickname(value: str) -> tuple[str, str]` returns normalized key and display name. `Round` dataclass stores UUID, nickname key/display, challenge, level, content version, questions, UTC start time, monotonic start value, answer records, cursor, and frozen completion fields. `start_round(nickname: str, challenge: str, level: str) -> Round`; `submit_answer(round: Round, question_id: str, choice_index: int) -> bool`; `advance(round: Round) -> bool`; `completed_result(round: Round) -> dict`.

- [x] Write tests for blank/overlength nicknames, Unicode normalization, invalid level/challenge, wrong/right answers, missing/out-of-range choices, repeated submissions, unanswered advance, and stale question IDs.
- [x] Assert a mixed three-correct round yields score `60`, accuracy `60`, five answer records, nonnegative duration, and identical completion timestamp on repeated result requests. An incomplete round must reject `completed_result`.
- [x] Run `python -m unittest discover -s tests -p test_game.py -v`; verify failures reflect absent rules.
- [x] Implement the interfaces with explicit state guards. Answer submission must match the current question ID, record once, and return whether accepted. Advance only after feedback for an answered question; freeze completion on the fifth accepted answer. Calculate duration from a monotonic clock and store UTC wall-clock timestamps separately.
- [x] Re-run the game tests and content tests; require all passing. Confirm no Streamlit import is needed for domain testing.

## Task 3: Durable, idempotent SQLite attempts

**Files:** Create `src/kidspark/storage.py`, `tests/test_storage.py`.

**Consumes:** `completed_result` dictionary with attempt metadata and five answer records.

**Produces:** `save_attempt(path: Path, result: dict) -> bool` returns true for a new insert, false for an identical existing attempt; `load_attempts(path: Path, nickname: str) -> list[dict]` returns completion-ordered results for the normalized nickname. Conflicting reuse of an ID raises `ValueError`. Each call initializes the schema if necessary.

- [x] Write temporary-database tests: save once, save the same result twice (one stored row), reopen via a fresh connection, separate two nicknames, safely handle SQL-looking nicknames, and reject incomplete/inconsistent results and conflicting attempt IDs.
- [x] Verify the loaded result includes challenge, level, score, accuracy, completion time, duration, content version, and answer-level skills. Assert an empty nickname history returns `[]`.
- [x] Run `python -m unittest discover -s tests -p test_storage.py -v`; expect missing implementation failures.
- [x] Implement an attempts table with primary-key attempt ID, metadata columns, and serialized answer records; use parameterized SQL, atomic transactions, explicit connection closure, and a busy timeout. Validate score/count/accuracy consistency before insertion. Compare existing content on retry instead of overwriting it.
- [x] Simulate inaccessible/invalid database paths and verify errors propagate to the UI rather than pretending success. Re-run storage and game tests; require all passing.

## Task 4: Progress calculations and recommendations

**Files:** Create `src/kidspark/progress.py`, `tests/test_progress.py`.

**Consumes:** `load_attempts` results and Task 1 constants.

**Produces:** `summarize_attempts(attempts: list[dict]) -> dict` with rounds, unique challenges, total score, correct/total, accuracy; `skill_accuracy(attempts: list[dict]) -> pd.DataFrame` with skill/correct/total/accuracy; `suggest_challenge(attempts: list[dict], level: str) -> tuple[str, str]` returns challenge and explanation.

- [x] Write tests asserting zero-valued empty summaries and empty skill schemas; unequal skill sample sizes yield weighted accuracy rather than average percentages; unique challenges never exceed three.
- [x] Assert suggestions prioritize untried challenges at the selected level, then lowest aggregate decision accuracy, with fixed challenge-order tie breaking. Results from the other level must not mark a selected-level challenge tried.
- [x] Run `python -m unittest discover -s tests -p test_progress.py -v`; verify expected failures.
- [x] Implement pure aggregation and deterministic recommendation interfaces. Preserve timestamp ordering and actual saved totals; never incorporate imported CSV data.
- [x] Re-run progress, storage, and game tests; require all passing.

## Task 5: Streamlit play-to-progress flow

**Files:** Modify `app.py`; create `src/kidspark/ui/__init__.py`, `src/kidspark/ui/app.py`, `src/kidspark/ui/play.py`, `src/kidspark/ui/progress.py`; adapt `tests/test_app.py`.

**Consumes:** Tasks 1â€“4 APIs.

**Produces:** `ui.app.main() -> None`, `ui.play.render_play(nickname: str, db_path: Path) -> None`, `ui.progress.render_progress(nickname: str, level: str, attempts: list[dict]) -> None`.

- [x] Write AppTest cases against a temporary `KIDSPARK_DB_PATH`: initial helpful empty state, invalid nickname, start round, no-choice submission, hint use without penalty, each answer and explanation, mixed-result completion, saved history visible on the same run, and fresh session recovery.
- [x] Exercise all six combinations through five decisions. Assert expected saved scores and exactly one history entry per completed round. Submit/re-run during feedback and completion; assert unchanged answer counts and database row counts.
- [x] Test nickname switch during a round and after completion, explicit start over, new attempt widget keys, storage save failure and retry with the original frozen timestamp. A second nickname must see no first-student attempts.
- [x] Run `python -m unittest discover -s tests -p test_app.py -v`; expect new flow assertions to fail before UI changes.
- [x] Implement top-level nickname input and the two named tabs. Bind active state to normalized nickname, lock challenge/level for an active round, and key answer widgets by attempt/question. Render one question, optional hint, feedback, Next, and explicit restart. Load history after the play renderer saves so progress refreshes immediately.
- [x] Render final score, accuracy, answer breakdown, duration, save/retry status, and a learning takeaway. Preserve completed state if storage fails. In My Progress reuse metric styles and two-column Plotly layout for skill accuracy and dated progress; add history, single-result handling, and suggested next challenge. Never interpolate student input into unsafe HTML.
- [x] Run AppTest and domain suites; require passing tests and no unexpected app exceptions. Use controls supported by the declared Streamlit version; prefer nondeprecated options where compatible.

## Task 6: Preserve CSV dashboard and finalize submission docs

**Files:** Move `metrics.py` to `src/kidspark/metrics.py`; create `src/kidspark/ui/imported.py`; update `tests/test_metrics.py`, `tests/test_app.py`, `README.md`; create `docs/architecture.md`, `docs/learning-content.md`, `docs/future-enhancements.md`; update the two ignored guides.

**Consumes:** Existing CSV metrics and Task 5 progress UI.

**Produces:** `render_imported(path: Path) -> None`, called within the Imported mission scores expander on My Progress.

- [x] Adapt existing CSV tests to package imports without changing their assertions. Add UI tests for normal imported scores, learner switching, header-only data, missing/invalid CSV, and launch from another working directory. Assert import errors do not block play or saved progress.
- [x] Run the targeted tests to observe import-view failures before extracting the original dashboard.
- [x] Extract the original CSV dashboard into its own renderer, retaining summaries, charts, leaderboard, and mission list with explicit fictional imported-data labeling. Keep errors/empty states local to this section.
- [x] Write the README with tested install/run/test commands, nickname identity, completion-only persistence, database override/backup, CSV customization, known limitations, and public documentation links. Do not link to Git-ignored guides from published docs.
- [x] Write architecture data-flow/state diagrams, actual schema and module responsibilities; learning-content descriptions and reviewed arithmetic; prioritized future enhancements clearly labeled unimplemented. Update local submission/video guides to match the actual UI and test evidence.
- [x] Run `python -m unittest discover -s tests -v`; record fresh date, interpreter/dependency versions, actual test count, and any relevant warnings. Tests must only touch temporary databases and restore working directories before cleanup.
- [x] Verify editable installation and root launch, inspect the final diff/files, and confirm `.gitignore` retains both local guides plus runtime-database exclusions. Do not stage or publish files. Report actual shipped features, test evidence, and nickname-authentication/persistent-disk limitations.
- [ ] Rehearse the five-minute screen sequence against the finished app. Keep the video a local recording guide; do not claim a video exists until the student records it.

## Plan self-review

All spec requirements map to the six tasks. Shared interfaces use the same names and result shapes throughout; tests cover all five review-focus failures. Package setup is paired with content delivery, and public documentation is paired with final verification. Local guides remain excluded from publication. No implementation or new-feature test success is claimed by this plan.


## Completed user-requested refinement
Simplified all thirty decisions with separate fact panels, redesigned My Progress with adventure cards and readable charts, and added a saved-result leaderboard. Rankings use best scores per challenge and separate school levels. Added storage, domain, and UI filter tests; nine demo rounds use an ignored, isolated database. Imported-score UI remains removed.
