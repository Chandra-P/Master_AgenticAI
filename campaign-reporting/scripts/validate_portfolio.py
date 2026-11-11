"""Read-only validation of all generated synthetic source files and persisted report facts."""

import gzip
import json
import sqlite3
from pathlib import Path


def main():
    root = Path("runtime")
    manifest = json.loads((root / "portfolio.json").read_text(encoding="utf-8"))
    assert len(manifest) == 50
    assert len({r["client_id"] for r in manifest}) == 50
    totals = {"households": 0, "digitally_reached": 0, "core_accounts": 0, "matches": 0}
    with sqlite3.connect(root / "runs.sqlite") as conn:
        for entry in manifest:
            with gzip.open(
                root / "sources" / (entry["client_id"] + ".json.gz"), "rt", encoding="utf-8"
            ) as stream:
                source = json.load(stream)
            assert source["client_id"] == entry["client_id"]
            assert len(source["audience"]) == 100000
            assert sum(h["digital_reached"] for h in source["audience"]) == 80000
            assert all(a["client_id"] == entry["client_id"] for a in source["accounts"])
            assert len({a["account_id"] for a in source["accounts"]}) == 760
            totals["households"] += len(source["audience"])
            totals["digitally_reached"] += sum(h["digital_reached"] for h in source["audience"])
            totals["core_accounts"] += len(source["accounts"])
            totals["matches"] += len(source["matches"])
            row = conn.execute(
                "SELECT data FROM report_runs WHERE run_id=? AND client_id=?",
                (entry["run_id"], entry["client_id"]),
            ).fetchone()
            assert row
            run = json.loads(row[0])
            for period, facts in run["facts"].items():
                assert sum(facts["channels"].values()) == facts["checking_accounts"]
                assert sum(b["accounts"] for b in facts["branches"]) == facts["checking_accounts"]
                assert sum(facts["product_mix"].values()) == facts["checking_accounts"]
                assert facts["direct_members"] + facts["halo_members"] == facts["new_members"]
                if period in ("30", "60", "90"):
                    assert facts["cpa"] is None
            assert run["approval"] is None and run["artifact"] is None
    print("Validated 50 clients and 250 reporting snapshots:", totals)


if __name__ == "__main__":
    main()
