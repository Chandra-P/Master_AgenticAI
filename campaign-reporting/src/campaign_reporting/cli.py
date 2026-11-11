import argparse
import gzip
import json
from dataclasses import asdict
from pathlib import Path

from .contracts import canonical
from .repository import Repository
from .runs import prepare_run
from .synthetic import generate_sources, portfolio_configs


def seed_portfolio(runtime, count=50, export_sources=True):
    runtime = Path(runtime)
    repo = Repository.local(runtime / "runs.sqlite")
    manifest = []
    for i, cfg in enumerate(portfolio_configs()[:count]):
        source = generate_sources(43 + i, cfg.client_id, config=cfg)
        run = prepare_run(repo, cfg, source=source)
        if export_sources:
            path = runtime / "sources" / f"{cfg.client_id}.json.gz"
            path.parent.mkdir(parents=True, exist_ok=True)
            # Stream one client's generated records at a time; do not hold 5 million household rows.
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                json.dump(asdict(source), stream, default=str, separators=(",", ":"))
        manifest.append(
            {
                "client_id": cfg.client_id,
                "brand": cfg.brand,
                "campaign_id": cfg.campaign_id,
                "digital_start": str(cfg.digital_start),
                "final_date": str(cfg.final_date),
                "run_id": run["run_id"],
                "checking_accounts": run["facts"]["F"]["checking_accounts"],
                "new_members": run["facts"]["F"]["new_members"],
                "status": run["status"],
            }
        )
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "portfolio.json").write_text(canonical(manifest), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Generate local fictional campaign data; no API calls.")
    parser.add_argument("command", choices=["seed"])
    parser.add_argument("--runtime", default="runtime")
    parser.add_argument("--clients", type=int, default=50, choices=range(1, 51))
    parser.add_argument("--no-source-export", action="store_true")
    args = parser.parse_args()
    result = seed_portfolio(args.runtime, args.clients, not args.no_source_export)
    print(f"Generated {len(result)} fictional clients. All runs await analyst review; API cost: $0.")


if __name__ == "__main__":
    main()
