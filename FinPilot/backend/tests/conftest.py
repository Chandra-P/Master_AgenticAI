import pytest
from finpilot.db import connect, migrate, seed


@pytest.fixture
def db(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    migrate(conn)
    seed(conn)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def offline_providers(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "deterministic")
    monkeypatch.setenv("COUNCIL_MODE", "off")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
