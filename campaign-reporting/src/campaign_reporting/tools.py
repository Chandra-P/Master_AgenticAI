import os
from dataclasses import replace
from pathlib import Path

from .observability import Telemetry
from .repository import Repository


class ReportTools:
    def __init__(self, repository, actor, telemetry=None):
        self.repo, self.actor = repository, replace(actor, role="narrative")
        if repository.db.dsn:
            dsn = os.environ.get("NARRATIVE_DATABASE_URL")
            if not dsn:
                raise PermissionError("narrative service requires its own scoped database identity")
            self.repo = Repository.postgres(dsn)
        root = Path(repository.path).parent if repository.path else Path("runtime")
        self.telemetry = telemetry or Telemetry(root / "telemetry.jsonl")

    def _read(self, run_id, name, select):
        with self.telemetry.span(name, run_id):
            return select(self.repo.get_run(self.actor, run_id))

    def get_metrics(self, run_id):
        return self._read(
            run_id,
            "get_metrics",
            lambda r: {
                "periods": r["facts"],
                "checking_accounts": r["facts"]["F"]["checking_accounts"],
                "goals": {"checking": r["config"]["checking_goal"], "members": r["config"]["member_goal"]},
            },
        )

    def get_rules_context(self, run_id):
        return self._read(
            run_id,
            "get_rules_context",
            lambda r: {
                "rules_version": r["rules_version"],
                "method": r["facts"]["F"]["method"],
                "limitations": r["facts"]["F"]["limitations"],
            },
        )

    def get_flag_status(self, run_id):
        return self._read(
            run_id,
            "get_flag_status",
            lambda r: {"requires_review": True, "correction": r["correction"], "review_mode": "all"},
        )

    def get_prior_version(self, run_id):
        def prior(run):
            rows = self.repo.list_runs(self.actor)
            found = [
                r
                for r in rows
                if r["campaign_id"] == run["campaign_id"]
                and r["version"] < run["version"]
                and r.get("status") == "delivered"
            ]
            return max(found, key=lambda r: r["version"])["facts"] if found else None

        return self._read(run_id, "get_prior_version", prior)
