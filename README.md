# Master_AgenticAI

A collection of AI-assisted learning projects, LangChain examples, and local AI tools.

## Projects

| Project | Description | Location |
| --- | --- | --- |
| KidSpark | Learning app for middle and high school students: budgeting, scam awareness, and event planning, with feedback, saved progress, and leaderboards. | [kidspark/](kidspark/) |
| Week 1: LangChain Fundamentals | Notebook covering prompts, chat models, streaming, chains, structured output, tools, and agents. Includes local Ollama examples and commented OpenAI examples. | [Notebook](Mastering-Agentic-AI-Week1/Langchain%20Basics/Langchain_Fundamentals.ipynb) |
| Terminal Web Chatbot | Local Ollama assistant with web search, source links, conversation memory, and geometry tools. | [terminal_chatbot.py](Mastering-Agentic-AI-Week1/Langchain%20Basics/terminal_chatbot.py) |
| Campaign Intelligence Hub | Week 2 RAG application using LangChain, local Ollama, ChromaDB, hybrid retrieval, and LangGraph. Generates cited direct mail/display campaign reports and compares performance with compatible historical campaigns. | [Project guide](Campaign-Intelligence-Hub/README.md) |
| Dhumsharath | React, Vite, and TypeScript Telugu movie dumb-charades game, with teams, timed rounds, hints, and scoreboards. | [Separate repository](https://github.com/Chandra-P/Dhumsharath) |

Dhumsharath remains a separate repository; cloning Master_AgenticAI does not include it.

## Repository structure

```text
Master_AgenticAI/
├── README.md
├── Campaign-Intelligence-Hub/
│   ├── app.py
│   ├── README.md
│   ├── src/
│   ├── tests/
│   ├── data/
│   └── docs/
│       ├── technical_solution_kit.html
│       └── campaign_performance_dashboard.html
├── kidspark/
│   ├── app.py
│   ├── README.md
│   ├── src/
│   ├── tests/
│   └── data/
└── Mastering-Agentic-AI-Week1/
    └── Langchain Basics/
        ├── Langchain_Fundamentals.ipynb
        ├── terminal_chatbot.py
        ├── langchain_prompts.py
        ├── README.md
        ├── pyproject.toml
        ├── uv.lock
        ├── env.demo
        └── images/
```

## Run KidSpark

Use Python 3.10 or newer. From the repository root:

```powershell
cd kidspark
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m streamlit run app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.
Open http://localhost:8501 if the browser does not open automatically.
See the [KidSpark guide](kidspark/README.md) for details.

## Run the Week 1 examples

Use Python 3.12 or newer. Install [Ollama](https://ollama.com/download), keep it running, and download the model:

```powershell
ollama pull llama3.2:3b
```

From the repository root:

```powershell
cd "Mastering-Agentic-AI-Week1/Langchain Basics"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install python-dotenv langchain langchain-core langchain-ollama ddgs ipykernel
```

On macOS/Linux, activate with `source .venv/bin/activate`. The install command includes the Ollama and web-search dependencies; the original project dependency file and lockfile still describe the earlier OpenAI setup.

### Notebook

Open `Langchain_Fundamentals.ipynb` in VS Code, select the new `.venv` interpreter as the notebook kernel, and run the cells in order. Use the active Ollama model cells; the previous OpenAI model examples are commented out.

The local examples need no OpenAI API key or `.env` file. Prompt-template examples work without a model server; generating answers requires Ollama and the downloaded model.

### Terminal web chatbot

From the same directory and environment:

```powershell
python terminal_chatbot.py
```

Ask a question at `You:` and press Enter. Enter `quit` or `exit` to stop. Conversation history lasts for the current process.

Web search requires internet access. The chatbot prints `Searching the web:` when searching and uses search snippets with source URLs, rather than full webpages. It can answer simple questions without searching.

## Dhumsharath

Source: [Chandra-P/Dhumsharath](https://github.com/Chandra-P/Dhumsharath). The application lives in `artifacts/dhumsharath/`; workspace details are in that repository's `replit.md`.

## Branch visibility

The Week 1 folder was added on `kidspark-final`. Select that branch on GitHub to see these additions until they are merged into `main`.
