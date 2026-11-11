"""Explicit local/replay/live evaluation entry point. Default mode never calls a provider."""

import argparse
import json
import os
from pathlib import Path

from campaign_reporting.evaluation.dataset import load_dataset
from campaign_reporting.evaluation.live import LiveTarget
from campaign_reporting.evaluation.results import EvaluationStore
from campaign_reporting.evaluation.runner import (
    EvaluationBlocked,
    compare_experiments,
    public_summary,
    run_experiment,
    summarize,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(Path(__file__).resolve().parents[1] / "evals"))
    parser.add_argument("--runtime", default="runtime")
    parser.add_argument("--mode", choices=("offline", "replay", "live"), default="offline")
    parser.add_argument("--split", choices=("development", "validation", "test"), default="development")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--experiment-id")
    parser.add_argument("--candidate-id", default="offline-baseline")
    parser.add_argument("--allow-heldout", action="store_true")
    parser.add_argument("--replay-file")
    parser.add_argument("--compare-with")
    parser.add_argument(
        "--oracle-experiment", help="Matching completed independent-oracle evidence for release review"
    )
    parser.add_argument("--summary-export")
    args = parser.parse_args()
    dataset = load_dataset(args.dataset)
    cases = dataset.select(args.split, args.allow_heldout, args.candidate_id)
    runtime = Path(args.runtime)
    target = None
    if args.mode == "live":
        target = LiveTarget(runtime)
    elif args.mode == "replay":
        if not args.replay_file:
            parser.error("--replay-file is required")
        records = {}
        for line in Path(args.replay_file).read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if item["case_id"] in records:
                    parser.error("duplicate replay case ID")
                records[item["case_id"]] = item["output"]

        def target(case):
            if case.case_id not in records:
                raise EvaluationBlocked("recorded output unavailable")
            return records[case.case_id]

    store = EvaluationStore(runtime / "evals/evaluations.sqlite")
    identity = run_experiment(
        store,
        cases,
        dataset_hash=dataset.manifest["dataset_hash"],
        mode=args.mode,
        target=target,
        repetitions=args.repetitions or (3 if args.mode == "live" else 1),
        experiment_id=args.experiment_id,
        candidate_id=args.candidate_id,
        split=args.split,
        allow_heldout=args.allow_heldout,
        model=os.environ.get("OPENAI_MODEL", "unconfigured") if args.mode == "live" else args.mode,
    )
    result = summarize(store, identity)
    if args.compare_with:
        result["comparison"] = compare_experiments(
            store, args.compare_with, identity, oracle_id=args.oracle_experiment
        )
    if args.summary_export:
        Path(args.summary_export).write_text(
            json.dumps(public_summary(store, identity), indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
