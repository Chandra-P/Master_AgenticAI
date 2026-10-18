# LangChain Basics

A hands-on demo project for Week 1, Session 2 of the Mastering Agentic AI Course. It covers LangChain fundamentals including prompt templates, chat models, and structured output using OpenAI.

## What's in the project

| File | Description |
|------|-------------|
| `Langchain_Fundamentals.ipynb` | Main demo notebook — prompts, chains, and structured output |
| `langchain_prompts.py` | Reusable prompt templates (date assistant, time-off extractor) |
| `env.demo` | Template for required environment variables |

## Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd langchain-basics
```

### 2. Create your environment file

```bash
cp env.demo .env
```

Then open `.env` and replace `your-openai-api-key-here` with your actual [OpenAI API key](https://platform.openai.com/api-keys).

### 3. Create a virtual environment and install dependencies

This project uses [uv](https://docs.astral.sh/uv/) for fast, reproducible installs.

```bash
# Install uv if you don't have it
pip install uv

# Create a virtual environment and sync from the lockfile
uv sync
```

### 4. Activate the virtual environment

```bash
source .venv/bin/activate
```

### 5. Run the notebook

```bash
jupyter notebook Langchain_Fundamentals.ipynb
```

Or open it directly in VS Code with the Jupyter extension.

## Requirements

- Python 3.12+
- An OpenAI API key
