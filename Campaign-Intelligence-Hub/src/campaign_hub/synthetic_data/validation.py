import json
from pathlib import Path
from .generator import digest


def validate_corpus(root: Path) -> list[str]:
    root = Path(root).resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    errors = []
    for doc in manifest['documents']:
        path = (root / doc['source_path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"Invalid source path: {doc['document_id']}")
        elif digest(path.read_text(encoding="utf-8")) != doc['content_hash']:
            errors.append(f"Changed source: {doc['document_id']}")
    return errors
