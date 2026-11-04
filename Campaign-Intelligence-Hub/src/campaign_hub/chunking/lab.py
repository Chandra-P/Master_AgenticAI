"""Inspect indexed chunks against the exact canonical text used by the chunker."""
import re
from campaign_hub.ingestion.markdown import sections
from campaign_hub.chunking.pipeline import STRATEGIES, tokens


def canonical_text(text):
    parts = list(sections(text))
    return '\n\n'.join(f'## {h}\n{b}' for h, b in parts) if parts else text.strip()


def _span(source, chunk, parts):
    meta = chunk.metadata
    start, end = meta.get('char_start'), meta.get('char_end')
    if isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(source):
        if source[start:end] == chunk.text:
            return start, end
    # Legacy fixed/section IDs encode a body-relative start; only trust a
    # parsed offset when slicing the canonical source reproduces the chunk.
    match = re.search(r':(fixed|section):[^:]*:(\d+):[a-f0-9]{8}$', chunk.chunk_id)
    if match:
        offset = int(match.group(2))
        bases = [0] if match.group(1) == 'fixed' else []
        cursor = 0
        for heading, body in parts:
            body_start = cursor + len(f'## {heading}\n')
            if match.group(1) == 'section' and heading == meta.get('section_name'):
                bases.append(body_start)
            cursor = body_start + len(body) + 2
        if not parts and match.group(1) == 'section':
            bases = [0]
        valid = [(base + offset, base + offset + len(chunk.text)) for base in bases
                 if source[base + offset:base + offset + len(chunk.text)] == chunk.text]
        if len(valid) == 1:
            return valid[0]
    occurrences = [m.start() for m in re.finditer('(?=' + re.escape(chunk.text) + ')', source)] if chunk.text else []
    if len(occurrences) == 1:
        return occurrences[0], occurrences[0] + len(chunk.text)
    return None, None


def describe_chunks(text, chunks):
    source = canonical_text(text)
    parts = list(sections(text))
    rows = []
    for chunk in chunks:
        start, end = _span(source, chunk, parts)
        rows.append({'chunk_id': chunk.chunk_id, 'text': chunk.text,
                     'token_count': len(tokens(chunk.text)), 'char_start': start,
                     'char_end': end, 'metadata': chunk.metadata})
    rows.sort(key=lambda r: (r['char_start'] is None, r['char_start'] or 0, r['chunk_id']))
    previous_end = None
    for row in rows:
        start, end = row['char_start'], row['char_end']
        overlap = None if start is None else (max(0, min(previous_end, end) - start) if previous_end is not None else 0)
        row['overlap_chars'] = overlap
        row['overlap_tokens'] = None if overlap is None else len(tokens(source[start:start + overlap]))
        if end is not None:
            previous_end = max(previous_end or 0, end)
    return rows


def inspect_source(service, document_id):
    metadata = next(d for d in service.manifest['documents'] if d['document_id'] == document_id)
    text = (service.settings.data / metadata['source_path']).read_text(encoding='utf-8')
    result = {'source': canonical_text(text), 'strategies': {}}
    for strategy in STRATEGIES:
        try:
            store = service.store(strategy)
            store.assert_compatible(service.corpus_hash)
            chunks = store.chunks({'document_id': document_id})
            if not chunks:
                raise ValueError('No indexed chunks for this source; rebuild this index.')
            result['strategies'][strategy] = {'chunks': describe_chunks(text, chunks)}
        except (ValueError, RuntimeError) as error:
            result['strategies'][strategy] = {'error': f'{strategy}: {error} Rebuild the {strategy} index, then inspect again.'}
    return result


def compare_evidence(service, query, options, campaign_id=None, filters=None):
    results = {}
    for strategy in STRATEGIES:
        try:
            selected = options.model_copy(update={'chunking': strategy})
            hits = service.search(query, campaign_id, selected, filters=filters or {})
            results[strategy] = {'hits': [hit.model_dump() if hasattr(hit, 'model_dump') else hit for hit in hits]}
        except (ValueError, RuntimeError) as error:
            results[strategy] = {'error': str(error)}
    return results

