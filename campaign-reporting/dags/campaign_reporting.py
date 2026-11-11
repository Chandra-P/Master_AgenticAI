"""Airflow 3 asset-aware entry points. Requires separate Airflow installation/metadata DB."""

from datetime import UTC, datetime

from airflow.exceptions import AirflowSkipException
from airflow.sdk import Asset, dag, task

ready = Asset("campaign-reporting://validated-synthetic-snapshots")


@dag(
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    tags=["synthetic", "readiness"],
)
def campaign_readiness():
    @task(outlets=[ready])
    def detect_change():
        import hashlib
        import os
        from pathlib import Path

        root = Path(os.environ["CAMPAIGN_RUNTIME"])
        manifest = root / "portfolio.json"
        if not manifest.exists():
            raise AirflowSkipException("No validated source manifest")
        fingerprint = hashlib.sha256(manifest.read_bytes()).hexdigest()
        marker = root / "airflow-last-manifest"
        if marker.exists() and marker.read_text() == fingerprint:
            raise AirflowSkipException("No source change")
        # Manifest contains only IDs and aggregate seed results; never place raw records in XCom.
        marker.write_text(fingerprint)
        return {"manifest_hash": fingerprint}

    detect_change()


@dag(
    schedule=[ready],
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    tags=["synthetic", "reporting"],
)
def campaign_reporting():
    @task
    def validate_and_prepare():
        import os
        from pathlib import Path

        from campaign_reporting.cli import seed_portfolio

        # Development adapter only. Production ingestion/claiming must use scoped Postgres workers.
        results = seed_portfolio(Path(os.environ["CAMPAIGN_RUNTIME"]), export_sources=False)
        return {"runs": len(results), "review_required": True}

    validate_and_prepare()


campaign_readiness()
campaign_reporting()
