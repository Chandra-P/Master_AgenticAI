# Master_AgenticAI

This repository is a portfolio-style collection of AI-assisted learning projects. The main project in this repo is KidSpark, a browser-based educational app that helps students practice real-world decision-making through short, game-like challenges.

## Project overview

KidSpark is built for middle and high school learners. Students work through short scenarios involving:

- budgeting
- scam awareness
- event planning

Each challenge includes guided choices, hints, explanations, progress tracking, and saved results so learners can practice practical judgment in a low-pressure environment.

## Important: where the app actually lives

The working project is nested in the `kidspark/` directory. The app entry file is:

- `kidspark/app.py`

If someone tries to run the app from the repository root without entering the nested project folder, they will hit the `File does not exist: app.py` issue that occurs when `app.py` is not present in the current working directory.

## Repository structure

- `README.md` — repo-level overview
- `kidspark/` — actual KidSpark project and application code
- `kidspark/README.md` — project-specific setup and usage guide
- `kidspark/app.py` — Streamlit app entry point
- `kidspark/data/` — local data and saved database files
- `kidspark/src/` — application code
- `kidspark/tests/` — automated validation tests

## How to recreate and run the app

From the repository root, either run the app directly with the nested path:

```powershell
streamlit run kidspark/app.py
```

Or enter the actual project folder first:

```powershell
cd .\kidspark
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m streamlit run app.py
```

On macOS/Linux:

```bash
cd kidspark
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m streamlit run app.py
```

## Why this project matters

KidSpark turns everyday decision-making into short learning experiences. Instead of passive reading, it helps students explore realistic trade-offs, evaluate information, and build confidence with practical problem-solving.

## Workflow and tools

This project was developed using Python, Streamlit, and an AI-assisted coding workflow. The application is structured to support iteration, testing, and rapid refinement while keeping the experience easy to use for students and reviewers.

## Status

This repository contains a working KidSpark app, supporting project documentation, and validated functionality for the challenge flow and learning experience.
