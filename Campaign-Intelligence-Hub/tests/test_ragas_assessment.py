import asyncio
from types import SimpleNamespace
from campaign_hub.models import FALLBACK,RetrievalOptions


class Metric:
    def __init__(self,value):self.value=value;self.samples=[]
    async def single_turn_ascore(self,sample):
        self.samples.append(sample)
        if isinstance(self.value,Exception):raise self.value
        return self.value


def test_actual_metric_scores_are_separate_and_nonfinite_or_failed_values_unavailable():
    from campaign_hub.evaluation.ragas_assessment import score_sample
    metrics={'ragas_faithfulness':Metric(.75),'ragas_context_precision':Metric(float('nan')),
             'ragas_context_recall':Metric(ValueError('secret request body'))}
    sample={'user_input':'Goal?','response':'180 activations.','retrieved_contexts':['Goal: 180 activations.'],'reference':'180 activations.'}
    result=asyncio.run(score_sample(sample,metrics,lambda **kw:SimpleNamespace(**kw)))
    assert result['ragas_faithfulness']==.75
    assert result['ragas_context_precision'] is result['ragas_context_recall'] is None
    assert set(result['metric_errors'])=={'ragas_context_precision','ragas_context_recall'}
    assert 'secret' not in str(result)
    assert metrics['ragas_faithfulness'].samples[0].response==sample['response']


def test_abstention_is_not_given_perfect_faithfulness():
    from campaign_hub.evaluation.ragas_assessment import score_sample
    metric=Metric(1.)
    result=asyncio.run(score_sample({'user_input':'Q','response':FALLBACK,'retrieved_contexts':['Evidence'],'reference':'A'},
        {'ragas_faithfulness':metric},lambda **kw:SimpleNamespace(**kw)))
    assert result['ragas_faithfulness'] is None and not metric.samples


def test_runner_captures_the_actual_generated_answer_and_exact_ranked_passages(tmp_path):
    import json
    from campaign_hub.config import Settings
    from campaign_hub.evaluation.ragas_assessment import run_assessment
    settings=Settings(root=tmp_path);(settings.data/'evaluation').mkdir(parents=True)
    cases=[{'id':'q1','kind':'question','split':'held_out','question':'Goal?','campaign_id':'C',
            'expected_answer':'180 activations.'},
           {'id':'q2','kind':'report','split':'held_out'}, {'id':'q3','kind':'question','split':'calibration'}]
    (settings.data/'evaluation/questions.json').write_text(json.dumps(cases))
    class Service:
        corpus_hash='version';settings=None
        def answer_question(self,*args):return {'answer':'180 activations. [chunk1]',
            'claims':[{'text':'180 activations.','citations':['chunk1']}],
            'hits':[{'chunk':{'chunk_id':'chunk1','text':'Goal: 180 activations.','metadata':{'document_id':'brief'}}}]}
    service=Service();service.settings=settings
    class Assessor:
        identity={'framework':'ragas','version':'test','judge_model':'judge'}
        def assess(self,sample):
            assert sample['response']=='180 activations. [chunk1]'
            assert sample['retrieved_contexts']==['Goal: 180 activations.']
            return {'ragas_faithfulness':.8,'ragas_context_precision':1.,'ragas_context_recall':1.,'metric_errors':{}}
    output=tmp_path/'runs'
    rows=run_assessment(service,output,[RetrievalOptions()],Assessor(),limit=1)
    assert len(rows)==1 and rows[0]['sample']['reference']=='180 activations.'
    assert rows[0]['chunk_ids']==['chunk1'] and rows[0]['identity']['corpus']=='version'
    assert rows[0]['ragas_faithfulness']==.8 and 'context_precision' not in rows[0]
    assert json.loads((output/'results.json').read_text())[0]['sample']==rows[0]['sample']


def test_cli_rejects_extractive_ragas_before_model_calls(monkeypatch,capsys):
    import pytest
    from campaign_hub.cli import main
    monkeypatch.setattr('sys.argv',['campaign_hub','evaluate','--ragas','--extractive'])
    with pytest.raises(SystemExit) as error:main()
    assert error.value.code==2 and 'generated answers' in capsys.readouterr().err


def test_judge_reuses_one_event_loop_for_consecutive_cases():
    from campaign_hub.evaluation.ragas_assessment import RagasAssessor
    loops=[]
    class LoopMetric:
        async def single_turn_ascore(self,sample):
            loops.append(asyncio.get_running_loop());return .5
    assessor=RagasAssessor.__new__(RagasAssessor)
    assessor.metrics={'ragas_faithfulness':LoopMetric()}
    assessor.sample_factory=lambda **kw:SimpleNamespace(**kw)
    assessor._runner=asyncio.Runner()
    sample={'user_input':'Q','response':'A','retrieved_contexts':['A'],'reference':'A'}
    with assessor:
        assert assessor.assess(sample)['ragas_faithfulness']==.5
        assert assessor.assess(sample)['ragas_faithfulness']==.5
        assert loops[0] is loops[1]
    assert loops[0].is_closed()
