import json
import sqlite3
import uuid
from pathlib import Path

from ..contracts import canonical
from ..repository import now
from .contracts import Annotation


class EvaluationStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS eval_experiments (
                  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS eval_cases (
                  experiment_id TEXT, case_id TEXT, client_id TEXT, data TEXT NOT NULL,
                  PRIMARY KEY(experiment_id,case_id));
                CREATE TABLE IF NOT EXISTS eval_attempts (
                  experiment_id TEXT, case_id TEXT, repetition INTEGER, status TEXT NOT NULL,
                  started INTEGER NOT NULL, result TEXT NOT NULL,
                  PRIMARY KEY(experiment_id,case_id,repetition));
                CREATE TABLE IF NOT EXISTS eval_annotations (
                  id TEXT PRIMARY KEY, experiment_id TEXT, case_id TEXT, repetition INTEGER,
                  actor_id TEXT, created_at TEXT, data TEXT NOT NULL);
            """)

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, metadata, cases, experiment_id=None):
        identity = experiment_id or str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT metadata FROM eval_experiments WHERE id=?", (identity,)
            ).fetchone()
            if existing:
                if json.loads(existing["metadata"]) != json.loads(canonical(metadata)):
                    raise ValueError("experiment provenance mismatch")
                return identity
            conn.execute(
                "INSERT INTO eval_experiments VALUES (?,?,?)", (identity, now(), canonical(metadata))
            )
            for case in cases:
                conn.execute(
                    "INSERT INTO eval_cases VALUES (?,?,?,?)",
                    (identity, case.case_id, case.client_id, case.model_dump_json()),
                )
        return identity

    def metadata(self, identity):
        with self.connect() as conn:
            row = conn.execute("SELECT metadata FROM eval_experiments WHERE id=?", (identity,)).fetchone()
        if not row:
            raise ValueError("unknown experiment")
        return json.loads(row["metadata"])

    def claim(self, identity, case_id, repetition):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "INSERT INTO eval_attempts VALUES (?,?,?,'claimed',0,'{}') ON CONFLICT DO NOTHING",
                (identity, case_id, repetition),
            )
            return cursor.rowcount == 1

    def start(self, identity, case_id, repetition):
        with self.connect() as conn:
            conn.execute(
                "UPDATE eval_attempts SET started=1 WHERE experiment_id=? AND case_id=? "
                "AND repetition=? AND status='claimed'",
                (identity, case_id, repetition),
            )

    def finish(self, identity, case_id, repetition, result):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "UPDATE eval_attempts SET status=?,started=?,result=? "
                "WHERE experiment_id=? AND case_id=? AND repetition=? AND status='claimed'",
                (result["status"], int(result["started"]), canonical(result), identity, case_id, repetition),
            )
            if cursor.rowcount != 1:
                raise ValueError("attempt terminal result is immutable")

    def rows(self, identity, actor=None):
        query = (
            "SELECT c.data,a.repetition,a.status,a.started,a.result FROM eval_cases c LEFT JOIN eval_attempts a "
            "ON c.experiment_id=a.experiment_id AND c.case_id=a.case_id WHERE c.experiment_id=?"
        )
        args = [identity]
        if actor is not None:
            query += " AND c.client_id=?"
            args.append(actor.client_id)
        with self.connect() as conn:
            records = conn.execute(query, args).fetchall()
            result = []
            for row in records:
                case = json.loads(row["data"])
                annotation = conn.execute(
                    "SELECT data,actor_id FROM eval_annotations WHERE experiment_id=? AND case_id=? "
                    "AND repetition=? ORDER BY rowid DESC LIMIT 1",
                    (identity, case["case_id"], row["repetition"]),
                ).fetchone()
                result.append(
                    {
                        "case": case,
                        "repetition": row["repetition"],
                        "status": row["status"],
                        "started": bool(row["started"]),
                        "result": json.loads(row["result"]) if row["result"] else {},
                        "annotation": json.loads(annotation["data"]) if annotation else None,
                    }
                )
        return result

    def experiments(self, actor):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT e.id,e.created_at,e.metadata FROM eval_experiments e JOIN eval_cases c "
                "ON c.experiment_id=e.id WHERE c.client_id=? ORDER BY e.created_at DESC",
                (actor.client_id,),
            ).fetchall()
        # Do not return global case/client lists through the analyst API.
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "mode": json.loads(row["metadata"])["mode"],
                "dataset_hash": json.loads(row["metadata"])["dataset_hash"],
            }
            for row in rows
        ]

    def annotate(self, actor, identity, case_id, repetition, annotation):
        annotation = Annotation.model_validate(annotation)
        if actor.role != "review":
            raise PermissionError("analyst annotation permission required")
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            case = conn.execute(
                "SELECT client_id FROM eval_cases WHERE experiment_id=? AND case_id=?", (identity, case_id)
            ).fetchone()
            if not case or case["client_id"] != actor.client_id:
                raise PermissionError("case is outside analyst client scope")
            attempt = conn.execute(
                "SELECT status FROM eval_attempts WHERE experiment_id=? AND case_id=? AND repetition=?",
                (identity, case_id, repetition),
            ).fetchone()
            if not attempt or attempt["status"] != "completed":
                raise ValueError("only completed attempts can be annotated")
            conn.execute(
                "INSERT INTO eval_annotations VALUES (?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    identity,
                    case_id,
                    repetition,
                    actor.actor_id,
                    now(),
                    annotation.model_dump_json(),
                ),
            )
