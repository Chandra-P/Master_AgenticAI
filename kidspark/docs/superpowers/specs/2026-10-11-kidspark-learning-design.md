# KidSpark interactive learning design

**Current refinement:** The approved fair-practice design and plan supersede
static questions, partial-participation overall ranking, and always-visible
leaderboard requirements in this historical document. See
[the fair-practice design](../specs/2026-10-11-kidspark-fair-practice-design.md).

**Scope update:** The user requested removal of the sample/imported-score dashboard.
The application now displays only played challenge results. Earlier CSV-view
requirements below are superseded; offline CSV utilities and tests remain.

## Purpose and approved scope

Turn the existing Streamlit score dashboard into a learning app for middle and
high school students. Students practice real-life decisions, receive an
explanation after each answer, and see their own saved results over time.
Reuse Streamlit, pandas, Plotly, the dashboard cards and charts, and the existing
CSV validation and mission metrics. No secrets or SSH keys will be read or
committed. This folder currently has no Git repository, so this document is
saved locally without a commit.

The project will be submitted as a Gen Academy assignment. The deliverable must
include a maintainable package structure, reproducible setup and test commands,
architecture and learning-content documentation, and a five-minute video guide
covering the idea, architecture, application walkthrough, and future enhancements.
The academy's specific grading rubric has not been supplied; do not invent it.

## Student identity

A nickname field above the two tabs selects the active student. Require 1–32
characters after trimming, and normalize with Unicode NFKC, collapsed
whitespace, and casefold for database lookup. Keep a readable display nickname.
The UI explains that students should choose distinct nicknames and reuse the
same nickname to return to their results. Different normalized nicknames have
separate histories; identical normalized nicknames intentionally share a
profile. Nicknames are identifiers, not authentication.

Changing nickname resets any in-memory round and immediately loads the newly
selected student's history. Blank or invalid nicknames cannot start a round.
Updated by user request: a cross-student leaderboard displays nicknames and best
scores only, separated by school level. Individual histories stay profile-scoped.

## Tab 1: Play Challenges

### Engagement and approachable difficulty

The experience should feel like helping with a small real-life adventure.
Introduce Smart Shopping as packing for a school outing, Spot the Scam as
helping a fictional friend check messages, and Plan an Event as organizing a
class celebration. Use a short scenario that connects the five decisions,
with a friendly opening and a celebratory finish. Decisions may share story
context, but each must provide all the information needed to answer it; a wrong
answer must not make later decisions harder or create an impossible budget.

Show one decision at a time. Keep prompts to one or two short sentences,
with no more than three concise choices in the initial question bank. Avoid
technical terminology unless it is explained beside the question. Prefer
small, familiar prices and explicit units. Students can use scratch work or a
calculator; no timed scoring, countdown, or speed ranking is used.

Within each round, begin with an easy confidence-building decision and increase
complexity gradually. Middle school questions use one-step calculations and
clear clues. High school questions may require two steps or closer evaluation
of evidence, but must state assumptions and avoid tricky wording. Success
depends on reasoning, not obscure knowledge or memorizing jargon.

Offer an optional Show hint control before submission. Hints explain the next
step without revealing the correct option. Using a hint does not reduce points.
Use a visible five-step progress indicator, a small contextual illustration or
emoji where helpful, and plain button labels. Do not add animation or visual
noise that makes the question harder to read.

After a correct answer, celebrate the decision briefly and explain why it
works. After a wrong answer, use neutral encouragement such as “Good try—let's
look at the clue,” then give the answer and a short explanation. Do not call
students careless, penalize them for taking time, or display comparisons with
other students. The final screen celebrates finishing and offers one concrete
learning takeaway and a clear option to try another round.

Before release, review prompts, choices, hints, and explanations for reading
load and ambiguous wording. Record educator or student feedback only if an
actual review takes place; do not describe the content as age-validated without
that evidence.

Choose Middle school or High school and one of Smart Shopping, Spot the Scam,
or Plan an Event. A brief description introduces each challenge. Start round
creates a unique attempt ID and fixes the nickname, school level, challenge,
question set, and start time for that round.

Each challenge has five multiple-choice decisions per school level: six
curated rounds and thirty decisions in total. Every decision has a stable ID,
skill label, three plausible choices, an optional hint, one correct answer, and an
explanation showing the calculation or reasoning. No live external content is
needed. Explanations must address the right choice and common mistakes.

### Challenge content

| Challenge | Middle school decisions | High school decisions |
| --- | --- | --- |
| Smart Shopping | Compare dollars per item; compare prices per equal volume; calculate a simple percentage discount; choose an affordable basket; recognize that the best unit price may exceed the budget. | Compare unequal package sizes with decimals; compare percentage and fixed discounts; apply successive discounts in order; add an explicit sales tax; compare total costs including delivery within a budget. |
| Spot the Scam | Identify a fictional prize scam; avoid sharing a password; check a sender through a known channel; question an unsupported claim; verify a suspicious link without opening it. | Detect an impersonated school payment request; verify an urgent account warning independently; recognize misleading sponsored claims; evaluate manipulated context in a screenshot; reject a request for a one-time verification code. |
| Plan an Event | Select an affordable venue and supplies; compute per-student snack costs; keep a reserve; compare two activity packages; check the final total. | Account for fixed and per-attendee costs; compare vendors with fees; apply an explicitly stated discount; reserve a percentage for contingencies; calculate a feasible ticket price or final budget balance. |

Skill labels are shared where appropriate (Unit prices, Discounts, Budgeting,
Verification, Privacy, Evaluating claims, Event planning). High school prompts
require more steps and more nuanced reasoning. All scam messages and claims
are explicitly fictional, with no clickable suspicious links.

### Answer flow and scoring

Show the decision number, prompt, choices, and a Submit answer button. No choice
is preselected. Submission requires a choice and records it only once for the
current decision. After submission, lock the answer, show correct/incorrect
feedback and the explanation, and offer Next decision. Feedback remains visible
until Next is pressed; a Streamlit rerun must not skip it.

Each correct decision earns 20 points: score is 0–100 and accuracy is correct
answers / 5 × 100. Wrong answers earn zero; speed does not affect score. Count
each answered decision once, including repeated clicks and reruns. Widget keys
include the attempt ID and decision ID to isolate old input from a new round.

After the fifth answer, show the final result, answer breakdown, and save status.
Automatically save the completed attempt before rendering My Progress in the
same run. Repeated saves with the same attempt ID have no additional effect.
Offer Play another round; starting again creates a new ID. A new deliberate
round is a new attempt, even for the same challenge and nickname.

An unfinished round lives in Streamlit session state, and is not counted as
completed or saved across a restart. Explicitly tell students that completed
rounds are saved. Level and challenge controls cannot silently change an active
round; changes apply only to the next round. Students can abandon a round with
an explicit Start over action, without creating a saved attempt.

## Durable storage

Use Python's standard-library sqlite3, with the default database at
`data/attempts.sqlite3` resolved relative to the app. A narrowly scoped
`KIDSPARK_DB_PATH` setting can override the location for tests or deployment.
Do not inspect unrelated environment variables or configuration files.

Store attempt ID (primary key), normalized nickname, display nickname,
challenge, school level, content version, score, correct count, question count,
accuracy, start timestamp, completion timestamp (UTC), elapsed seconds, and
answer records including decision ID, skill, selected answer, and correctness.
Completion time is frozen on first completion and reused on save retries.
Use an atomic transaction and parameterized SQL. An existing attempt ID never
overwrites another student or changes the original result.

Validate complete attempts before inserting. Use fresh short-lived connections
with a busy timeout; close every connection. A database error produces a useful
message and preserves the finished round in memory with a Retry save action.
Never claim a round is saved until the transaction succeeds. History is always
queried for the current normalized nickname, without a global history cache.

Completed results survive app/server restarts while the database file exists.
On a deployment with ephemeral disk, a persistent writable disk is required.
Document the database location, backup by copying it while the app is stopped,
and nickname identity behavior. Exclude database files, their journal files,
virtual environments, and Python caches from version control.

## Tab 2: My Progress

Before the first completed game, show zero summary values and a friendly
invitation to try a challenge. Do not substitute fictional CSV scores for game
results.

For the current student, show:

- Completed rounds and distinct challenges completed out of three.
- Total score and overall accuracy (correct decisions / all decisions).
- Accuracy by skill, aggregated from saved answer records rather than averaging
  skill percentages with different denominators.
- Score and accuracy over time with completion timestamps and challenge/level
  context, including a useful single-result display.
- A history table with challenge, school level, score, accuracy, completion
  timestamp, and duration.
- Suggested next challenge: first recommend an untried challenge at the selected
  level, then the challenge with the lowest saved decision accuracy at that
  level. Use the fixed challenge order for ties; explain the recommendation.

Reuse the existing metric-card treatment and two-column Plotly chart layout.
Use clear middle/high-school wording. Render stored nicknames and content as
text; do not interpolate them into unsafe HTML.

## Existing CSV dashboard

Keep `metrics.py`, its validation fixes, and `data/missions.csv` supported.
Move the original dashboard into an expandable Imported mission scores section
within My Progress. Preserve explorer selection, summary metrics, category
charts, leaderboard, and mission table. Clearly label the bundled dataset as
fictional imported data, separate from the active student's game history.
Missing or invalid CSV data affects only this section and cannot block gameplay
or access to saved game results. Header-only CSV data keeps its empty state.
Continue the existing local-file import workflow; no upload subsystem is needed.

## Project organization and module responsibilities

Use a Python `src` package layout, with a thin root Streamlit entry point:

```text
kidspark/
  app.py
  pyproject.toml
  requirements.txt
  .gitignore
  README.md
  src/kidspark/
    __init__.py
    config.py
    challenges.py
    game.py
    storage.py
    progress.py
    metrics.py
    ui/
      __init__.py
      app.py
      play.py
      progress.py
      imported.py
  data/
    missions.csv
  tests/
    test_challenges.py
    test_game.py
    test_storage.py
    test_progress.py
    test_metrics.py
    test_app.py
  docs/
    architecture.md
    learning-content.md
    submission-guide.md
    video-guide.md
    future-enhancements.md
    superpowers/specs/
```

- Root `app.py`: calls the package's Streamlit application entry point.
- `config.py`: resolves app data paths and the database override.
- `challenges.py`: versioned question data, level and challenge definitions.
- `game.py`: round creation, one-time answer submission, scoring, completion.
- `storage.py`: SQLite schema initialization, idempotent inserts, student reads.
- `progress.py`: saved-result summaries, skill aggregation, recommendation.
- `metrics.py`: existing CSV validation and mission calculations, moved into
  the package with tests and UI imports updated together.
- `ui/`: Streamlit presentation and session-state integration, separated from
  domain calculations and storage. Imported mission scores have their own view.
- `tests/`: domain, persistence, CSV regression, and Streamlit flow tests.
- `pyproject.toml`: package metadata, Python requirement, runtime dependencies,
  and build configuration. `requirements.txt` delegates to an editable local
  install, keeping dependency declarations in one place.

The README will provide Windows and macOS/Linux setup, `pip install -e .`,
`streamlit run app.py`, `python -m unittest discover -s tests -v`, example
nickname usage, both tabs, database persistence, CSV customization, known
limitations, and links to the documents above. Keep the commands executable
from a clean checkout. Use type hints for public domain/storage APIs and
docstrings for behavior and invariants; avoid comments that repeat the code.

Documentation requirements:

- Architecture: module boundaries, state transitions, data flow, SQLite schema,
  idempotency, nickname isolation, and storage tradeoffs, with a diagram.
- Learning content: the six rounds, skills, scoring, explanation strategy,
  numerical answer review, and distinction between the two school levels.
- Submission guide: a reviewer entry point, acceptance checklist, verified test
  evidence, packaging instructions excluding runtime data and secrets, and
  links to the video guide. Do not claim tests or features are complete until
  they have been verified against the implementation.
- Video guide: an exactly five-minute timeline with narration and screen cues,
  including a full five-decision round, feedback, saved progress, nickname
  separation, architecture, limitations, and future enhancements.
- Future enhancements: prioritized proposals clearly marked unimplemented,
  including authenticated profiles, a larger question bank, adaptive difficulty,
  teacher reporting, accessibility improvements, and persistent hosting.

The draft submission and video guides can be prepared now. Finalize their
feature claims, commands, screenshots if used, and test evidence only after
implementation verification. Do not include speculative assignment grades or
claim the application is ready for public multi-user deployment.

No new runtime dependency is expected beyond the existing three packages.
Use the installed Streamlit reference documentation before implementation and
ensure widgets remain compatible with the declared minimum version, or update
that minimum explicitly if required.

## Acceptance and verification

1. All six challenge/level combinations contain exactly five valid decisions,
   nonempty explanations, and one valid correct choice each. Review every
   calculation and scam explanation for accuracy and appropriate difficulty.
   Every decision has a useful hint and at most three concise choices. Verify
   that hints do not change scoring, later questions remain solvable after a
   wrong answer, and feedback stays encouraging.
2. Submit an answer twice: answer count and score change only on the first
   submission. Reruns preserve feedback and cannot skip unanswered decisions.
3. Complete all five decisions through Streamlit AppTest and verify the exact
   result appears in My Progress and in SQLite. Include mixed correct and wrong
   answers, an all-correct round, and repeat completion/save attempts.
4. Launch a fresh app session against the same temporary database and recover
   the saved result. A second nickname has an empty history; changing nickname
   midway through a round never attributes answers to the new student.
5. Verify nickname normalization, invalid nickname handling, parameterized
   storage, incomplete-attempt rejection, and save-failure/retry behavior.
6. Verify weighted skill accuracy, progress timestamps, recommendation ordering,
   and helpful empty/single-result dashboard states.
7. Existing CSV calculation tests continue passing. Adapt dashboard tests to
   target the imported section; missing or invalid CSV cannot stop the game.
8. App launches from another working directory. Tests restore the working
   directory before Windows temporary-folder cleanup.
9. Run `python -m unittest discover -s tests -v` with temporary databases so tests
   do not create or modify real student histories. Report any remaining warnings
   or execution limitations accurately.
10. Verify editable installation, root entry point, package imports, documented
    setup commands, and test discovery after reorganizing the code. The final
    docs must match actual paths, behavior, and test evidence.
11. Rehearse the video guide against the finished UI and fit the demonstration
    within five minutes. The guide is a recording aid, not a claim that a video
    has been recorded.

## Spec review

The approved design is reflected in both tabs, persistence, separated nickname
histories, CSV compatibility, and complete-flow tests. Score and accuracy use
the same denominator throughout. Restart persistence applies to completed
attempts, not unfinished rounds. No unresolved design placeholders remain.
