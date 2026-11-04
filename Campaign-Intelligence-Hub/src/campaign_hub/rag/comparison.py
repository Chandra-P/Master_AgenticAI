"""Offline experiment summaries, never campaign report generation."""
from statistics import mean


def paired_reranking(rows):
    groups = {}
    for row in rows:
        key = tuple(row[k] for k in ('split', 'chunking', 'retrieval'))
        groups.setdefault(key, {False: {}, True: {}})[row['reranking']][row['case_id']] = row
    summaries = []
    for key, states in groups.items():
        before, after = states[False], states[True]
        common = before.keys() & after.keys()
        pairs = [(before[c], after[c]) for c in sorted(common)
                 if not before[c].get('error') and not after[c].get('error')]
        summary = dict(zip(('split', 'chunking', 'retrieval'), key))
        summary.update(paired_successes=len(pairs),
                       before_failures=sum(bool(r.get('error')) for r in before.values()),
                       after_failures=sum(bool(r.get('error')) for r in after.values()),
                       unpaired_cases=len(before.keys() ^ after.keys()))
        for metric, name in [('context_precision', 'precision_delta'),
                             ('context_recall', 'recall_delta'), ('mrr', 'mrr_delta'),
                             ('latency_seconds', 'latency_delta_seconds')]:
            values = [b[metric] - a[metric] for a, b in pairs
                      if a.get(metric) is not None and b.get(metric) is not None]
            summary[name] = mean(values) if values else None
        summaries.append(summary)
    return summaries
