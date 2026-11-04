# CONVENE

AI course MVP: six LangGraph agents produce an event plan through a FastAPI API
and Streamlit UI. Target working end-to-end: **November 2, 2026**.
Submission deadline: **November 5, 2026**.

Synthetic estimates only. No real bookings or payments. All amounts are USD.
Demo mode requires no API keys and makes no external AI or retrieval calls.
The six agents are graph nodes; in demo they are deterministic. In live mode,
Vendor uses OpenAI embeddings and Pinecone RAG; Creative uses an OpenAI model.
Other nodes remain deterministic for predictable constraint checking.

## Windows / VS Code

Open this folder in VS Code. Use Python 3.12 or newer. In PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn convene.api:app --reload
```

Leave the API terminal open. In a second terminal, from the same folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open http://localhost:8501. The API docs are at http://localhost:8000/docs.
Create a Seattle event with 40 guests and a $5,000 budget. Download the resulting
plan JSON or load saved plans. SQLite persists plans in `data/convene.db`.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

On Linux/macOS, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.
Run all commands from the project root. Do not expose the API publicly: this
course MVP has no authentication, per-user isolation, or rate limits.

## Optional live mode

1. Put your own keys into `.env` (never commit it).
2. Create a Pinecone index with 1536 dimensions and cosine metric; set
   `PINECONE_INDEX` to its name.
3. Run `python -m scripts.seed_pinecone` with your virtual-environment Python.
   This explicitly uploads only the synthetic vendor catalog and incurs costs.
4. Set `CONVENE_MODE=live`, `OPENAI_API_KEY`, and `PINECONE_API_KEY`. Restart API.
5. To opt into traces, set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.
   LangGraph supports LangSmith tracing natively. Traces may contain event inputs;
   use synthetic inputs for the course. Paid services are not required for demo.

Live service failures return an error rather than silently switching to demo.
Vendor matches are checked against the local synthetic catalog; retrieved content
cannot introduce real vendors. Pinecone similarity is not an availability check.

## GitHub handoff

No repository or valid GitHub connection was available at creation time. These
files have not been committed or pushed. Do not assume this cloud folder syncs
to Windows. Download the source ZIP, extract it, and copy the files into your
intended CONVENE checkout (including `.github`, `.gitignore`, `.env.example`).

```powershell
git clone https://github.com/YOUR-ACCOUNT/CONVENE.git
cd CONVENE
# Copy project source here, then verify the remote before staging:
git remote -v
git status --short
git add .
git diff --cached --stat
git commit -m "Build CONVENE six-agent course MVP"
git push
```

Verify the staged files contain no credentials or local databases. Alternatively,
connect the intended repository to this Codex cloud environment to continue here.

## Layout and API

- `convene/models.py`: input validation
- `convene/workflow.py`: six-agent LangGraph workflow
- `convene/integrations.py`: demo catalog and optional OpenAI/Pinecone adapters
- `convene/storage.py`: SQLite persistence
- `convene/api.py`: `POST /plans`, `GET /plans`, `GET /plans/{id}`, `GET /health`
- `streamlit_app.py`: create, view and export plans
- `tests/test_app.py`: API and workflow acceptance tests
- `docs/architecture.md`, `docs/milestones.md`: design and delivery scope

See `docs/verification.md` for actual cloud verification results and limitations.
