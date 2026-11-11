"""Regenerate the pinned synthetic evaluation dataset. No provider/network calls."""

from pathlib import Path

from campaign_reporting.evaluation.dataset import build_dataset

if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "evals"
    data = build_dataset(target)
    print(
        f"Built {len(data.cases)} cases; hash {data.manifest['dataset_hash']}; semantic labels need human review."
    )
