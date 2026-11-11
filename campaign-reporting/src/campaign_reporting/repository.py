"""Persistent operational repository; SQLite is a local harness, Postgres is the deployment adapter."""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .contracts import canonical

SCHEMA = """
CREATE TABLE IF NOT EXISTS report_runs (
 run_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
 identity_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
 status TEXT NOT NULL, version INTEGER NOT NULL,
 data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
 event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, client_id TEXT NOT NULL,
 action TEXT NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS campaign_configs (
 config_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
 confirmed_by TEXT NOT NULL, confirmed_at TEXT NOT NULL, data TEXT NOT NULL
);
"""


def now():
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    client_id: str
    role: str


class Database:
    def __init__(self, path=None, dsn=None):
        self.path, self.dsn = path, dsn

    @contextmanager
    def transaction(self):
        if self.dsn:
            import psycopg
            from psycopg.rows import dict_row

            conn = psycopg.connect(self.dsn, row_factory=dict_row)
        else:
            conn = sqlite3.connect(self.path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, conn, query, args=()):
        return conn.execute(query.replace("?", "%s") if self.dsn else query, args)


class Repository:
    def __init__(self, database):
        self.db = database
        self.path = database.path

    @classmethod
    def local(cls, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = cls(Database(path=path))
        with result.db.transaction() as conn:
            conn.executescript(SCHEMA)
        return result

    @classmethod
    def postgres(cls, dsn):
        # Schema provisioning is deliberately an explicit operator action.
        return cls(Database(dsn=dsn))

    def audit(self, conn, actor, run_id, action):
        self.db.execute(
            conn,
            "INSERT INTO audit_events VALUES (?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                run_id,
                actor.client_id,
                action,
                actor.actor_id,
                now(),
            ),
        )

    def get_run(self, actor, run_id):
        with self.db.transaction() as conn:
            table = "narrative_runs" if self.db.dsn and actor.role == "narrative" else "report_runs"
            row = self.db.execute(
                conn, f"SELECT data FROM {table} WHERE run_id=? AND client_id=?", (run_id, actor.client_id)
            ).fetchone()
            if not row:
                raise PermissionError("run unavailable for this actor")
            result = json.loads(row["data"])
            # Narrative can read facts/config, never draft feedback or reviewer identity.
            if actor.role == "narrative":
                return {
                    k: result[k]
                    for k in (
                        "run_id",
                        "client_id",
                        "campaign_id",
                        "facts",
                        "config",
                        "rules_version",
                        "correction",
                        "version",
                        "status",
                    )
                }
            return result

    def list_runs(self, actor):
        with self.db.transaction() as conn:
            table = "narrative_runs" if self.db.dsn and actor.role == "narrative" else "report_runs"
            rows = self.db.execute(
                conn,
                f"SELECT data FROM {table} WHERE client_id=? ORDER BY created_at DESC",
                (actor.client_id,),
            ).fetchall()
            results = [json.loads(r["data"]) for r in rows]
            if actor.role == "narrative":
                keys = {
                    "run_id",
                    "client_id",
                    "campaign_id",
                    "facts",
                    "config",
                    "rules_version",
                    "correction",
                    "version",
                    "status",
                }
                return [{k: v for k, v in row.items() if k in keys} for row in results]
            return results

    def mutate(self, actor, run_id, update):
        if actor.role not in ("review", "compute", "delivery"):
            raise PermissionError("role cannot modify report")
        with self.db.transaction() as conn:
            query = "SELECT data FROM report_runs WHERE run_id=? AND client_id=?"
            if self.db.dsn:
                query += " FOR UPDATE"
            row = self.db.execute(conn, query, (run_id, actor.client_id)).fetchone()
            if not row:
                raise PermissionError("run unavailable for this actor")
            result = json.loads(row["data"])
            action = update(result)
            self.db.execute(
                conn,
                "UPDATE report_runs SET data=?, status=? WHERE run_id=? AND client_id=?",
                (canonical(result), result["status"], run_id, actor.client_id),
            )
            self.audit(conn, actor, run_id, action)
            return result

    def save_config(self, actor, config):
        from dataclasses import asdict

        from .contracts import digest

        if actor.role != "review" or actor.client_id != config.client_id:
            raise PermissionError("configuration confirmation denied")
        data = asdict(config)
        identity = digest(data)
        with self.db.transaction() as conn:
            self.db.execute(
                conn,
                "INSERT INTO campaign_configs VALUES (?,?,?,?,?,?) ON CONFLICT(config_id) DO NOTHING",
                (identity, config.client_id, config.campaign_id, actor.actor_id, now(), canonical(data)),
            )
        return identity
