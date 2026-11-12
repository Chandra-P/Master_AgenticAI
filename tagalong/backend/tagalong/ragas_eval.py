"""Ragas evaluation helpers that stay out of Tagalong's API runtime path."""
import asyncio
import math
import sys
from types import ModuleType
from statistics import mean


def _context_text(item):
    origin = item.get('retrieval_origin', 'unknown')
    title = item.get('title', 'Untitled evidence')
    text = item.get('text', '')
    return f'[{origin}] {title}: {text}'


def _response_text(output):
    lines = [f"Verdict: {output.get('verdict', 'unknown')}", output.get('summary', '')]
    for label in ('matches', 'conflicts'):
        lines.extend(f"{label.title()}: {item.get('text', '')}" for item in output.get(label, []))
    lines.extend(f"Unknown: {item}" for item in output.get('unknowns', []))
    return '\n'.join(line for line in lines if line)


def build_ragas_sample(case, evidence, output):
    """Build Ragas inputs from synthetic case data and the actual model prompt evidence."""
    option = case.get('option', {})
    plan_facts = next((item.get('text', '') for item in evidence if item.get('retrieval_origin') == 'postgres'), '')
    user_input = '\n'.join((
        'Assess whether this proposed option fits the group.',
        f"Option: {option.get('name', '')}",
        f"Details (user-provided): {option.get('details', '')}",
        f"Estimated cost per person: {option.get('estimated_cost_per_person', 'not supplied')}",
        f'Current plan facts: {plan_facts}',
    ))
    return {
        'case_id': case['id'],
        'user_input': user_input,
        'response': _response_text(output),
        'prompt_contexts': [_context_text(item) for item in evidence if item.get('text')],
        'pinecone_contexts': [
            _context_text(item) for item in evidence
            if item.get('retrieval_origin') == 'pinecone' and item.get('text')
        ],
        'reference': case.get('constraints'),
    }


def _metric_fields(name, row):
    fields = {'user_input': row['user_input']}
    if name == 'faithfulness':
        fields.update(response=row['response'], retrieved_contexts=row['prompt_contexts'])
    elif name == 'answer_relevancy':
        fields['response'] = row['response']
    elif name in ('context_precision', 'context_recall'):
        fields.update(retrieved_contexts=row['pinecone_contexts'], reference=row['reference'])
    else:
        raise ValueError(f'Unsupported Ragas metric: {name}')
    return fields


def _score_value(result):
    value = getattr(result, 'value', result)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Ragas returned a non-numeric score')
    return float(value)


def _install_ragas_vertexai_compat():
    """Provide Ragas 0.4.3's removed, unused Vertex import for OpenAI scoring."""
    import importlib.util
    vertex_module = 'langchain_community.chat_models.vertexai'
    try:
        spec = importlib.util.find_spec(vertex_module)
    except (ImportError, ModuleNotFoundError, ValueError):
        spec = None
    if spec is None:
        compatibility_module = ModuleType(vertex_module)
        compatibility_module.ChatVertexAI = type('ChatVertexAIUnavailable', (), {})
        sys.modules[vertex_module] = compatibility_module


async def score_ragas_rows(rows, metrics, sample_factory):
    """Score prepared rows; isolate metric failures and return JSON-safe aggregates."""
    cases = []
    values = {name: [] for name in metrics}
    errors = {name: 0 for name in metrics}
    for row in rows:
        case_result = {'case_id': row['case_id'], 'metrics': {}}
        for name, metric in metrics.items():
            if name in ('context_precision', 'context_recall') and not row.get('reference'):
                case_result['metrics'][name] = {'status': 'skipped', 'reason': 'reference_missing'}
                continue
            try:
                sample = sample_factory(**_metric_fields(name, row))
                raw_score = await metric.single_turn_ascore(sample)
                score = _score_value(raw_score)
                values[name].append(score)
                case_result['metrics'][name] = {'status': 'scored', 'score': score}
            except Exception as error:
                errors[name] += 1
                case_result['metrics'][name] = {
                    'status': 'error', 'error_type': type(error).__name__
                }
        cases.append(case_result)

    aggregate = {
        name: {
            'mean': round(mean(scores), 4) if scores else None,
            'scored_cases': len(scores),
            'errors': errors[name],
        }
        for name, scores in values.items()
    }
    has_errors = any(errors.values())
    return {
        'status': 'partial' if has_errors else 'completed',
        'cases': cases,
        'aggregate': aggregate,
    }


async def score_with_ragas(rows, api_key, judge_model, embedding_model):
    """Create Ragas 0.4 metrics lazily so normal API/test imports stay lightweight."""
    # Ragas 0.4.3 imports a Vertex AI class from a langchain-community module
    # that was removed when that integration moved to its own package. Tagalong
    # evaluates only with OpenAI, so expose a non-matching placeholder for that
    # optional provider. This mirrors the upstream optional-import fix without
    # installing an unrelated Vertex AI client into the evaluation environment.
    _install_ragas_vertexai_compat()

    from openai import AsyncOpenAI
    from ragas.dataset_schema import SingleTurnSample
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

    client = AsyncOpenAI(api_key=api_key)
    llm = llm_factory(judge_model, client=client)
    embeddings = embedding_factory('openai', model=embedding_model, client=client)
    metrics = {
        'faithfulness': Faithfulness(llm=llm),
        'answer_relevancy': AnswerRelevancy(llm=llm, embeddings=embeddings),
        'context_precision': ContextPrecision(llm=llm),
        'context_recall': ContextRecall(llm=llm),
    }
    try:
        return await score_ragas_rows(rows, metrics, SingleTurnSample)
    finally:
        await client.close()


def score_with_ragas_sync(rows, api_key, judge_model, embedding_model):
    return asyncio.run(score_with_ragas(rows, api_key, judge_model, embedding_model))
