import re
from pathlib import Path
from campaign_hub.models import SourceDocument
from campaign_hub.synthetic_data.validation import validate_corpus


def load_documents(root: Path, manifest: dict) -> list[SourceDocument]:
    errors = validate_corpus(root)
    if errors:
        raise ValueError('; '.join(errors))
    return [SourceDocument(metadata=d, text=(root/d['source_path']).read_text(encoding='utf-8')) for d in manifest['documents']]


def sections(text):
    for match in re.finditer(r'^## (.+)\n([\s\S]*?)(?=^## |\Z)', text, re.MULTILINE):
        yield match.group(1), match.group(2).strip()


def anchor(heading):
    return re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
