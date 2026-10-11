# KidSpark

KidSpark is an interactive learning app for middle and high school students.
Students make five small decisions in a real-life story, learn from immediate
explanations, and return to their own saved progress.

## What students can do

| Challenge | Story | Skills |
| --- | --- | --- |
| Smart Shopping | Pack for a school outing | Unit prices, discounts, budgets |
| Spot the Scam | Help a fictional friend check messages | Verification, privacy, evaluating claims |
| Plan an Event | Organize a class celebration | Event costs, reserves, budget decisions |

**Play Challenges** provides two school levels, five decisions per round,
three choices per decision, optional free hints, and encouraging feedback.
Short fact panels separate the prices, budget, or pretend message from the question.
Each correct decision earns 20 points, with no time pressure or speed bonuses.
Repeated answers and repeated saves cannot count twice. Each new deliberate
round is a separate attempt.

**My Progress** shows completed rounds, challenges explored, points, weighted
accuracy by skill, history over time, and a suggested next challenge. Its empty
state invites a student to play their first round. All these values come from
actual saved game results.
Challenge cards show each adventure's best result at the selected school level.
Challenge cards show first, latest, and best scores plus completion badges.
Finish all three adventures at the selected level to earn an explorer badge.
The optional leaderboard adds each nickname's best score per challenge, up to
300 points, and ranks overall results only after all three challenges are
completed at that level. Individual challenge rankings are available sooner.
Middle and high school rankings are separate. Equal totals share a rank.

## Run locally

Use Python 3.10 or newer and a terminal in the project root, beside `app.py`.
A source checkout with an editable installation is the supported setup.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m streamlit run app.py
```

If PowerShell activation is restricted, use the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m streamlit run app.py
```

`python -m pip install -r requirements.txt` is equivalent to the editable install:
runtime dependencies are declared once in `pyproject.toml`.
Open **http://localhost:8501** if the browser does not open automatically.
Stop the server with Ctrl+C. When launching from another directory, pass the
absolute path to `app.py`; data paths still resolve against the source checkout.

## Try the complete flow

1. Enter a fictional, distinct nickname such as `Orion Demo`.
2. Choose a school level and Smart Shopping, then select **Start round**.
3. Answer each decision; try **Show hint** and read the explanation before Next.
4. Finish all five decisions and confirm the successful save message.
5. Open **My Progress** to see the new round, skill accuracy, and recommendation.
   Check your completion badge and first/latest/best scores. Select **Show
   leaderboard** if you want to view rankings; choose a single challenge before
   you have completed all three.
6. Enter a different nickname to see its separate history.
7. Restart the app and reuse the first nickname to recover its saved results.

Use a calculator or scratch paper if helpful. Wrong answers do not make later
questions harder. Unfinished rounds reset if you leave or change nickname.

## Saving and student profiles

Completed attempts are stored in `data/attempts.sqlite3`, created on first
history access or save. Each includes nickname, challenge, school level, score,
accuracy, start/completion timestamps, elapsed seconds, and skill-level answers.
UTC timestamps and duration are recorded, but speed never affects points.
The progress chart and history display Chicago time, with daylight saving
adjustments; timestamps in storage remain UTC.

Nicknames are normalized for whitespace, Unicode width, and capitalization:
`Orion Demo` and ` orion  demo ` refer to the same profile. Choose a unique
nickname with 1–32 characters. Nicknames separate histories but do not authenticate
students; someone who uses the same nickname can see those results. No real
names or private details are needed for the local demonstration.
Leaderboard nicknames and best scores are visible to other app users. Choose a
fictional nickname you are comfortable sharing; individual answers are not on
the leaderboard.
Hiding the leaderboard controls viewing, not publication of your nickname's
eligible best scores. It is hidden by default to emphasize personal learning.

Completed results survive app restarts while the database file exists. Unfinished
rounds do not. If a save fails, keep the page open and use **Retry save** before
leaving or changing nickname. A hosted deployment needs persistent writable disk.
Stop the app before copying its SQLite database for a simple backup.

To use a separate demo database, set the supported setting before launching:

```powershell
$env:KIDSPARK_DB_PATH = "$PWD/data/demo.sqlite3"
python -m streamlit run app.py
```

```bash
KIDSPARK_DB_PATH="$PWD/data/demo.sqlite3" python -m streamlit run app.py
```

Tests use temporary databases and do not change student histories.

## Project organization

The thin root `app.py` calls `kidspark.ui.app.main`. Application code lives in
`src/kidspark/`: `challenges.py` defines learning content, `game.py` owns round
rules, `storage.py` owns SQLite, `progress.py` calculates history metrics, and
`metrics.py` retains offline legacy CSV utilities. `ui/` contains the three Streamlit views. The app only displays played challenge results.

- [Architecture and data flow](docs/architecture.md)
- [Learning content and reviewed answers](docs/learning-content.md)
- [Verification evidence](docs/verification.md)
- [Future enhancements](docs/future-enhancements.md)

## Verify

With the editable package installed, run from the project root:

```bash
python -m unittest discover -s tests -v
```

The suite checks all six UI rounds, wrong answers and hints, one-time answer/save
handling, restart recovery, profile separation, save retries, skill calculations,
recommendations, offline CSV utility regressions, and launching from another directory.
See the verification document for the actual environment and latest test count.

## Scope and limitations

This is a local learning demonstration with ninety curated decisions. Each
round selects one of three variants for each of five learning objectives; the
introductory decision stays first and the others vary in order. Variants change
amounts or fictional messages while retaining comparable reasoning steps.
Questions can repeat; randomized practice is not proof of understanding.
There is no account system, teacher portal,
AI-generated content, live scam analysis, or hosted deployment. The question
bank has an author-level review but has not been tested with students or an
educator, so it is not claimed to be age-validated.

Future priorities include usability and accessibility evaluation, authenticated
profiles, more question variants, adaptive practice, and persistent hosting.
The project does not require credentials. Runtime databases, environments,
caches, and secret files are excluded from version control.
