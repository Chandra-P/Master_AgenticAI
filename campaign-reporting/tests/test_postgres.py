"""Optional real-Postgres boundary tests; never substitute SQLite for these checks."""

import os

import pytest

pytestmark = pytest.mark.postgres


def test_narrative_login_cannot_read_raw_sources():
    dsn = os.environ.get("TEST_POSTGRES_NARRATIVE_DSN")
    if not dsn:
        pytest.skip("Postgres narrative test identity is not provisioned on this host")
    import psycopg

    with psycopg.connect(dsn) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("SELECT payload FROM source_snapshots LIMIT 1")
    with psycopg.connect(dsn) as conn:
        rows = conn.execute("SELECT DISTINCT client_id FROM narrative_runs").fetchall()
        allowed = conn.execute("SELECT reporting_client()").fetchone()[0]
        assert allowed
        assert all(row[0] == allowed for row in rows)
        attrs = conn.execute(
            "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        assert attrs == (False, False)
