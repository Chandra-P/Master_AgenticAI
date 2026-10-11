"""Paths for the source-checkout application and its durable data."""
import os
from pathlib import Path


def data_directory() -> Path:
    """Find bundled mission data independently of the working directory."""
    return Path(__file__).resolve().parents[2] / 'data'


def database_path() -> Path:
    """Use only the explicitly supported database setting."""
    override = os.environ.get('KIDSPARK_DB_PATH', '').strip()
    return Path(override).expanduser().resolve() if override else data_directory() / 'attempts.sqlite3'
