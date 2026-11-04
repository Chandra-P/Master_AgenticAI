# CONVENE agent instructions

Course deadline: November 5, 2026. Prioritize a working end-to-end demo by November 2.
Use Python 3.12+, FastAPI, Streamlit and LangGraph. Six nodes: Requirements,
Budget, Vendor, Schedule, Creative, Review. Keep demo mode independent of API keys.
Use only synthetic vendor data. Do not implement bookings, purchases or payments.
Never commit .env, keys, SQLite files, virtual environments or personal event data.
Run `python -m pytest -q` before claiming tests pass. Report actual output.
Verify `git remote -v` points to the user's intended CONVENE repository before
committing or pushing. Do not initialize or alter the workspace's protected .git.
Document changes to setup and API behavior. Live calls incur costs and may trace
user inputs if LangSmith tracing is enabled; keep it disabled by default.
