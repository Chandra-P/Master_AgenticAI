"""Isolated helpers for live synthetic retrieval evaluation."""
import copy
import time

from .core import source


def create_synthetic_source(repo, plan_id, source_id, title, text):
    if not isinstance(source_id, str) or not source_id.startswith('eval-'):
        raise ValueError('Synthetic source IDs must start with eval-')
    repo.transact(lambda state: source(state, plan_id, source_id, title, text, kind='message'))
    return copy.deepcopy(repo.state['sources'][plan_id + ':' + source_id])


def mark_synthetic_source_indexed(repo, source_record):
    source_key = source_record['plan_id'] + ':' + source_record['id']

    def mark(state):
        current = state['sources'].get(source_key)
        if not current or current['version'] != source_record['version'] or current['deleted']:
            raise ValueError('Synthetic source changed before indexing completed')
        jobs = [job for job in state.get('jobs', {}).values()
                if job.get('source_key') == source_key and job.get('version') == current['version']]
        if not jobs:
            raise ValueError('Synthetic source indexing job was not found')
        for job in jobs:
            job['status'] = 'done'

    repo.transact(mark)


def remove_synthetic_source(repo, source_record):
    if not source_record.get('id', '').startswith('eval-'):
        raise ValueError('Only synthetic evaluation sources can be removed')
    source_key = source_record['plan_id'] + ':' + source_record['id']

    def remove(state):
        state.get('sources', {}).pop(source_key, None)
        jobs = state.get('jobs', {})
        for job_id in [key for key, job in jobs.items() if job.get('source_key') == source_key]:
            jobs.pop(job_id, None)

    repo.transact(remove)


def wait_for_pinecone_sources(provider, plan_id, query, expected_source_ids, timeout=20,
                              interval=0.5, present=True):
    """Wait for specified synthetic sources to appear or disappear from semantic top-k."""
    expected = set(expected_source_ids)
    if not expected:
        raise ValueError('At least one expected synthetic source ID is required')
    if not plan_id or not plan_id.replace('-', '').isalnum():
        raise ValueError('Evaluation plan ID is invalid')
    client = provider.client.with_options(timeout=8, max_retries=0)
    vector = provider.embedding(query, client=client)
    namespace = 'tagalong:' + plan_id
    deadline = time.monotonic() + timeout
    latest = []
    while True:
        response = provider.index.query(namespace=namespace, vector=vector, top_k=6,
                                        include_metadata=True, _request_timeout=8)
        latest = []
        for match in response.matches:
            metadata = match.metadata or {}
            latest.append({'source_id': metadata.get('source_id', match.id),
                           'score': getattr(match, 'score', None)})
        found = {item['source_id'] for item in latest} & expected
        if bool(found) == present:
            return {'namespace': namespace, 'expected_source_ids': sorted(expected),
                    'retrieved_source_ids': [item['source_id'] for item in latest],
                    'matched_source_ids': sorted(found), 'scores': latest}
        if time.monotonic() >= deadline:
            message = ('Synthetic evidence did not appear in Pinecone top-k results' if present
                       else 'Deleted synthetic evidence remained in Pinecone top-k results')
            raise TimeoutError(message)
        time.sleep(interval)


def cleanup_synthetic_sources(provider, sources):
    """Delete only supplied synthetic source IDs; return failed IDs without provider details."""
    failed = []
    for item in sources:
        try:
            provider.delete(item)
        except Exception:
            failed.append(item['id'])
    return failed


def compare_ablation_responses(with_body, without_body, source_id):
    """Measure cited evidence and substantive output changes, separately from verdict changes."""
    expected = 'saved:' + source_id

    def findings(body):
        return body.get('matches', []) + body.get('conflicts', [])

    cited_with = any(expected in finding.get('source_ids', []) for finding in findings(with_body))
    cited_without = any(expected in finding.get('source_ids', []) for finding in findings(without_body))

    def content(body):
        return {
            'matches': [(item.get('text'), tuple(item.get('source_ids', []))) for item in body.get('matches', [])],
            'conflicts': [(item.get('text'), tuple(item.get('source_ids', []))) for item in body.get('conflicts', [])],
            'unknowns': tuple(body.get('unknowns', [])),
        }

    changed = content(with_body) != content(without_body)
    return {
        'pinecone_evidence_cited_with_source': cited_with,
        'pinecone_evidence_cited_after_removal': cited_without,
        'response_content_changed': changed,
        'evidence_materially_changed_response': cited_with and not cited_without and changed,
        'verdict_changed': with_body.get('verdict') != without_body.get('verdict'),
    }
