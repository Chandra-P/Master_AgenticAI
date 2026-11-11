import json
import uuid
from dataclasses import asdict
from pathlib import Path

from .compute import compute_report_facts
from .contracts import canonical, digest
from .readiness import check_readiness
from .repository import ActorContext, now
from .synthetic import generate_sources


def prepare_run(repo, config, seed=42, source=None):
    source = source or generate_sources(seed, config.client_id, config=config)
    readiness = check_readiness(source, config)
    if not readiness["ready"]:
        raise ValueError("sources not ready: " + ",".join(readiness["issues"]))
    cfg = asdict(config)
    compute_version = digest((Path(__file__).parent / "compute.py").read_text(encoding="utf-8"))
    identity = digest([readiness["snapshot_id"], cfg, config.rules_version, compute_version])
    # Computing before transaction is safe: identity uniqueness and claim serialize persistence.
    facts = {p: compute_report_facts(source, config, p).public_dict() for p in ("30", "60", "90", "120", "F")}
    actor = ActorContext("pipeline", config.client_id, "compute")
    with repo.db.transaction() as conn:
        if repo.db.dsn:
            # Serialize all claims for a campaign, including different snapshots.
            repo.db.execute(
                conn,
                "SELECT pg_advisory_xact_lock(hashtext(?))",
                (config.client_id + ":" + config.campaign_id,),
            )
        existing = repo.db.execute(
            conn, "SELECT data FROM report_runs WHERE identity_hash=?", (identity,)
        ).fetchone()
        if existing:
            return json.loads(existing["data"])
        row = repo.db.execute(
            conn,
            "SELECT COUNT(*) AS n FROM report_runs WHERE client_id=? AND campaign_id=?",
            (config.client_id, config.campaign_id),
        ).fetchone()
        version = row["n"] + 1
        run = {
            "run_id": str(uuid.uuid4()),
            "client_id": config.client_id,
            "campaign_id": config.campaign_id,
            "identity_hash": identity,
            "snapshot_id": readiness["snapshot_id"],
            "compute_version": compute_version,
            "config": cfg,
            "rules_version": config.rules_version,
            "facts": facts,
            "version": version,
            "status": "computed",
            "correction": version > 1,
            "created_at": now(),
            "draft": None,
            "draft_hash": None,
            "approval": None,
            "artifact": None,
            "revision": 0,
        }
        repo.db.execute(
            conn,
            "INSERT INTO report_runs VALUES (?,?,?,?,?,?,?,?)",
            (
                run["run_id"],
                config.client_id,
                config.campaign_id,
                identity,
                run["created_at"],
                run["status"],
                version,
                canonical(run),
            ),
        )
        repo.audit(conn, actor, run["run_id"], "run_claimed")
        return json.loads(canonical(run))
