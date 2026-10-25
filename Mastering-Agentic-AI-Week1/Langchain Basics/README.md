# LangChain Basics

A hands-on demo project for Week 1, Session 2 of the Mastering Agentic AI Course. It covers prompts, chat models, structured output, tools, and agents using local Ollama models.

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

The template selects `llama3.2:3b` at `http://localhost:11434`. No OpenAI key is needed. Start Ollama and run `ollama pull llama3.2:3b` once.

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

On Windows PowerShell use `.\.venv\Scripts\Activate.ps1`.

### 5. Run the notebook

```bash
uv run python -m ipykernel install --user --name langchain-basics --display-name "Week 1 (Ollama)"
```

Open the notebook in VS Code with the Jupyter extension and select this project's `.venv`. Run the cells in order. The final chatbot cell waits for input; type `quit` to finish it. For the terminal web chatbot, run `uv run python terminal_chatbot.py`. Web search needs internet access; model inference stays local.

## Requirements

- Python 3.12+
- Ollama running with `llama3.2:3b` installed
