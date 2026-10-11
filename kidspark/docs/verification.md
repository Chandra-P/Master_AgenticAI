# KidSpark verification

## Executed checks

On October 11, 2026, the full suite ran successfully with:

```text
python -m unittest discover -s tests -v
Ran 46 tests
OK
```

Environment: Windows, Python 3.12.10, Streamlit 1.65.0, pandas 2.3.3, Plotly 6.9.0.
The editable source package installed successfully with `python -m pip install -e .`.
`python -m pip check` reported no broken requirements. A headless Streamlit server
started on localhost and returned HTTP 200 `ok` from its health endpoint before
being stopped. Package imports resolved to this checkout's `src/kidspark`.

| Area | Evidence |
| --- | --- |
| Learning content | Six combinations, five decisions each, 90 unique definitions, three variants per objective, valid answers, bounded reading load, reproducible balanced selection |
| Game rules | Nickname normalization, answer/advance guards, no duplicate scoring, frozen completion, new attempt IDs |
| SQLite | Actual temporary-database inserts and reopens, identical-save idempotency, conflict rejection, profile separation, version-1 fixture compatibility/retries, mixed-version records, duplicate-objective and foreign-ID rejection |
| Progress | Real-result summaries, weighted skill accuracy, selected-level recommendations, ordered first/latest/best/change, lower latest scores, and deterministic ties |
| Leaderboard | Best-score aggregation, repeated-play handling, shared ranks, nickname grouping, school-level separation, all-three eligibility, challenge filter, actual UI results, default-hidden query-free view, zero-score badges and explorer completion |
| Interactive flow | All six rounds played via Streamlit AppTest; explanations, mixed/all-correct results, immediate dashboard updates, fresh-session recovery, failed-save retry |
| CSV compatibility | Offline calculation/regression checks; sample-score UI removed by request. Other-directory app launch remains covered. |

The six full rounds are subcases within one UI test, so the test-method count
does not equal the number of individual assertions or round scenarios. New
modules and flow tests were first run against the missing behavior, then against
their implementations. Arithmetic was also checked against the answer guide.

## Execution limits

### Ten-user stored-results test

An additional October 11 run played all three challenges through AppTest for
ten fictional profiles, five at each school level. Two profiles also replayed
Shopping with a lower score: 32 persisted attempts and 160 decisions in total.
Every profile recovered its expected history in a fresh app session; reruns
did not duplicate saves, lower replays preserved best scores, and both boards
had ranks 1, 2, 2, 4, 5 with totals 300, 240, 240, 180, 140.
Results are retained locally under ignored `data/test-runs/ten-users-m64xvpmx/`:
SQLite with full answer records, an attempt-summary CSV, separate school-level
leaderboard CSVs, and a JSON check report. This is a sequential automated UI
test, not a simultaneous ten-user load test or a student usability study.

### Earlier checks and tooling limits

Eight additional AppTest rounds used a fresh ignored demo database. Demo
Ava and Demo Cora tied at rank 1 with 240/300 after completing all three middle-
school challenges. Demo Ben completed Shopping at 100 and appeared only in
that individual ranking. Ava improved Shopping from 60 to 80; the first/latest/
best card and 20-point change matched the saved history. High-school rankings
remained empty. No student database was modified.

Independent review checked all 90 questions and found no critical or important
issues. Two minor findings (articles in choices and displaying negative score
change) were corrected; a new regression test failed before the delta fix and
passed in the final 46-test suite. The local server returned HTTP 200 `ok`. Browser visual inspection was
blocked by the computer-use sandbox and is not claimed.

The local interpreter is inaccessible inside this session's filesystem sandbox;
test commands were run with approved access to the existing Python installation.
No student database was used for verification; each storage and app test used a
temporary path. Streamlit emits a `missing ScriptRunContext` warning for the
AppTest setup thread; no unexpected app exceptions or deprecated-width warnings
appeared in the passing suite.

AppTest verifies rendered elements, interactions, calculations, and persistence.
It is not a browser accessibility audit, student usability study, or a timed
video rehearsal. A real five-minute recording and academy-specific submission
review remain the student's final preparation steps. The declared minimum
versions have not been independently tested in this environment.
The updated local narration contains approximately 501 words. Timing at
an assumed 140 words per minute is only a recording-planning estimate.
The actual spoken rehearsal remains an outstanding video-preparation step.
