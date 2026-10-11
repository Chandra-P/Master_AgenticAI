# KidSpark: fair practice and progress

## Intent and approved scope

Improve the existing assignment app so rankings compare equal participation,
replays practice reasoning, and personal learning takes priority over competition.
The user approved the recommended scope without accounts. Keep Streamlit, the
two tabs, SQLite persistence, five decisions, free hints, and existing histories.
Do not publish assignment guides, read secrets, or modify real student results.

## Decisions

### Fair comparisons

Overall rankings include only nicknames with completed results in all three
challenges at the selected school level. Rank by the sum of best scores, maximum
300; equal totals share a rank. A student with one or two challenges sees an
encouraging eligibility message and personal completion progress, not an overall
rank. Individual-challenge rankings remain available immediately after finishing
that challenge. Middle and high school never share a ranking. Replaying cannot
add leaderboard points unless the best score improves. Speed is never a factor.

An average of unequal participation was rejected because one perfect round
could outrank three strong rounds. Difficulty weighting was rejected because
there is no calibrated evidence for numeric weights. Equal participation plus
comparable authored rounds is transparent for this assignment.

### Varied, comparable rounds

Expand the bank from 30 to 90 reviewed questions: three variants of each of the
five learning objectives in each challenge/level combination. Keep each objective
represented exactly once per round. Change numbers or message context while
keeping the objective, calculation steps, reading load, and defensible answer
comparable. Preserve short fact panels, one direct task, three options, hints,
and explanations. No generated questions or external services are needed.

Select one variant per objective when a round starts. Keep the introductory
objective first and shuffle the other four. Use the attempt ID as a reproducible
random seed. Freeze questions throughout the round; reruns and retry-save cannot
change them. Choices stay in their authored order to keep answer validation
simple. Randomization reduces memorization but does not guarantee unseen
questions or demonstrate student understanding.

Use an explicit difficulty rubric: middle school uses familiar amounts, one
main calculation or obvious checking clue; high school can use two calculation
steps or compare source/context evidence. Match corresponding variants to this
rubric. Educational difficulty still needs student/educator evaluation; the app
must not claim calibrated or age-validated difficulty.

### Saved-answer compatibility

Archive the existing version-1 bank without changing IDs, correct indices, or
skills. New rounds use version 2. Validate version-2 results by question ID in
the selected challenge/level bank, not by fixed tuple position. Require exactly
five distinct questions, one per objective, valid selected indices, matching
skills/correctness, and consistent totals. Reject wrong-level, wrong-challenge,
duplicate-objective, and unsupported-version records.

Existing version-1 records remain readable and identical save retries remain
valid. No SQLite schema change or destructive migration is necessary: existing
answers already store question IDs, selected indices, correctness, and skills;
attempts already store content version. Both versions contribute to personal
history and best-score rankings, with the same five-question scoring rules.

### Learning before competition

Add a Show leaderboard checkbox, off by default. Do not query or render public
rankings when it is off. This controls viewing, not publication: saved nickname
best scores remain eligible for the shared leaderboard. Explain this distinction
near the control and retain the public-nickname notice.

Each challenge card shows first, latest, and best scores at the selected school
level, plus latest-minus-first change in points. Use ordered saved records,
including completion-time/attempt-ID tie breaking. A single result shows no
comparison yet; a lower latest score receives neutral practice copy. Do not
call score changes proven mastery. All-history totals and skill accuracy remain
clearly labeled as such.

Award a completion badge for each finished challenge regardless of score and
an explorer badge after all three at the selected level. Show badges for all
students, independent of rank. These are computed from saved attempts; no badge
table is required. Keep empty states helpful and make the next challenge easy
to identify.

### Identity boundary

Nicknames remain local identifiers, not verified students or private accounts.
Do not claim that the multiple-profile or impersonation drawback is solved.
Document authenticated profiles, access control, and account recovery as future
work before real classroom deployment. Use fictional nicknames for demos.

## Files and tests

Extend `challenges.py` with the versioned bank and objective metadata;
`game.py` with reproducible round selection; `storage.py` with version-aware
question validation; `progress.py` with eligibility and first/latest/best
summaries; and `ui/progress.py` with badges and optional rankings. Keep the thin
launcher, dashboard framework, and SQLite schema.

Verify all 90 question definitions and reviewed answer calculations; all six
round combinations; seeded variant diversity and stable in-round questions;
one-per-objective selection; valid shuffled-result saves; historical version-1
retry/reopen; malformed-answer rejection; full-completion overall eligibility;
individual filters and ties; separate levels; first/latest/best ordering;
default-hidden rankings; badges including zero-score completion; full
play-to-progress persistence, duplicate submission guards, and save retries.

Update architecture, learning-content, README, verification, and future-work
documents. Update local video/submission guides while keeping them ignored.
Use temporary/ignored demo databases. Run the full test suite and an independent
final code review before reporting completion. Browser/student evaluation is a
separate check and must only be claimed if actually performed.

## Limits

This design addresses participation fairness, static-question memorization,
hidden progress, and mandatory competition. Authenticated identity, empirical
difficulty calibration, and proof of understanding remain future work. No
weighted average can substitute for those checks.
