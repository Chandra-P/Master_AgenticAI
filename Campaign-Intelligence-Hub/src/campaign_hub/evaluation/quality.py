"""Explicit 90% gates with assessment coverage, not a blended quality score."""
import math
from statistics import mean


def configure_evaluation_key(path):
    """Load only the owner key from an ignored TOML file, without logging it."""
    import os,tomllib
    from pathlib import Path
    if os.getenv('GROQ_API_KEY'):return
    path=Path(path)
    if not path.is_file():return
    try:
        data=tomllib.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError,OSError) as error:
        raise ValueError('Evaluation secrets file could not be parsed; check its TOML syntax.') from None
    key=data.get('GROQ_API_KEY')
    if key is not None:
        if not isinstance(key,str) or not key.strip():raise ValueError('GROQ_API_KEY must be a nonempty string.')
        os.environ['GROQ_API_KEY']=key.strip()

QUALITY_METRICS=('passage_relevance_precision','ragas_context_recall','ragas_faithfulness','ragas_factual_correctness')


def passage_precision(verdicts,expected_count):
    if not expected_count or len(verdicts)!=expected_count:return None
    values=[v['verdict'] for v in verdicts]
    if any(v not in (0,1) for v in values):return None
    return sum(values)/len(values)


def quality_summary(rows,expected_supported,expected_unsupported,target=.9):
    if not 0<target<=1:raise ValueError('Target must be in (0, 1]')
    by_id={r['case_id']:r for r in rows}
    if len(by_id)!=len(rows):raise ValueError('Summarize one configuration without duplicate cases')
    supported=[by_id[c] for c in expected_supported if c in by_id]
    unsupported=[by_id[c] for c in expected_unsupported if c in by_id]
    metrics={}
    for name in QUALITY_METRICS:
        values=[r[name] for r in supported if not r.get('error') and isinstance(r.get(name),(int,float))
                and not isinstance(r[name],bool) and math.isfinite(r[name]) and 0<=r[name]<=1]
        metrics[name]={'mean':mean(values) if values else None,'measured':len(values),'expected':len(expected_supported)}
    coverage=sum(not r.get('error') and not r.get('abstained',True) for r in supported)/len(expected_supported) if expected_supported else None
    abstention=sum(not r.get('error') and r.get('abstained',False) for r in unsupported)/len(expected_unsupported) if expected_unsupported else None
    incomplete=(not expected_supported or len(supported)!=len(expected_supported) or len(unsupported)!=len(expected_unsupported)
        or any(m['measured']!=m['expected'] for m in metrics.values()) or any(r.get('error') for r in rows)
        or any(r.get('judge_calibration_passed') is not True for r in supported))
    passes=(not incomplete and coverage>=target and all(m['mean']>=target for m in metrics.values())
        and (abstention is None or abstention>=target))
    status='incomplete' if incomplete else 'target_met_on_evaluated_set' if passes else 'below_target'
    return {'target':target,'status':status,'metrics':metrics,'answer_coverage':coverage,
            'unsupported_abstention_accuracy':abstention,
            'judge_calibration_passed':bool(supported) and all(r.get('judge_calibration_passed') is True for r in supported),
            'note':'Developmental model assessment on a narrow synthetic set; not independent certification or production accuracy.'}
