from campaign_hub.rag.grounding import generation_prompt_identity
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
            'hits':[{'chunk':{'chunk_id':'chunk1','text':'Goal: 180 activations.','metadata':{'document_id':'brief'}},'score':1.0}]}
    service=Service();service.settings=settings
    class Assessor:
        identity={'framework':'ragas','version':'test','judge_model':'judge','judge_calibration':{'passed':True}}
        def assess(self,sample):
            assert sample['response']=='180 activations. [chunk1]'
            assert [json.loads(c) for c in sample['retrieved_contexts']]==[
                {'id':'chunk1','text':'Goal: 180 activations.'}]
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


def test_interrupted_run_checkpoints_current_rows_instead_of_stale_results(tmp_path):
    import json,pytest
    from campaign_hub.config import Settings
    from campaign_hub.evaluation.ragas_assessment import run_assessment
    settings=Settings(root=tmp_path);(settings.data/'evaluation').mkdir(parents=True)
    cases=[{'id':name,'kind':'unsupported','split':'held_out','question':'Unsupported?',
            'expected_answer':'Unavailable','campaign_id':'C'} for name in ['u1','u2']]
    (settings.data/'evaluation/questions.json').write_text(json.dumps(cases))
    calls=[]
    def answer(*args):
        calls.append(1)
        if len(calls)>1:raise KeyboardInterrupt
        return {'answer':FALLBACK,'hits':[]}
    service=SimpleNamespace(settings=settings,corpus_hash='version',answer_question=answer)
    assessor=SimpleNamespace(identity={'judge_calibration':{'passed':True}})
    out=tmp_path/'runs';out.mkdir();(out/'results.json').write_text('[{"case_id":"stale"}]')
    with pytest.raises(KeyboardInterrupt):
        run_assessment(service,out,[RetrievalOptions()],assessor,limit=2,quality=True)
    assert [r['case_id'] for r in json.loads((out/'results.json').read_text())]==['u1']
    assert json.loads((out/'quality-summary.json').read_text())[0]['status']=='incomplete'


def test_openai_judge_uses_langchain_adapter_without_generator_model(monkeypatch):
    from campaign_hub.evaluation.ragas_assessment import create_judge_model
    from campaign_hub.config import Settings
    import langchain_openai
    captured={}
    def adapter(**kwargs):captured.update(kwargs);return object()
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',adapter)
    monkeypatch.setenv('OPENAI_API_KEY','private-test-value')
    create_judge_model(Settings(),provider='openai',model='gpt-4.1-mini')
    assert captured['model']=='gpt-4.1-mini'
    assert captured['temperature']==0
    assert 'api_key' not in captured


def test_uncalibrated_metric_values_are_not_reported():
    from campaign_hub.evaluation.quality import quality_summary
    row={'case_id':'q','error':None,'abstained':False,'ragas_faithfulness':1.,
         'ragas_context_recall':1.,'ragas_factual_correctness':1.,'passage_relevance_precision':1.}
    result=quality_summary([row],['q'],[])
    assert result['metrics']['ragas_faithfulness']['mean'] is None


def test_current_ragas_loader_rejects_changed_cases_and_uncalibrated_rows(tmp_path,monkeypatch):
    import json,hashlib
    from campaign_hub.config import Settings
    from campaign_hub.ui.current_ragas_results import load_current_ragas
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    settings=Settings(root=tmp_path)
    cases=[{'id':'q','kind':'question','split':'held_out','question':'Goal?',
            'expected_answer':'180','expected_sources':['brief']}]
    (settings.data/'evaluation').mkdir(parents=True)
    path=settings.data/'evaluation/questions.json';path.write_text(json.dumps(cases))
    embedder=SimpleNamespace(identity={'provider':'test','model':'test'})
    monkeypatch.setattr('campaign_hub.embeddings.providers.create_embedder',lambda _:embedder)
    service=SimpleNamespace(settings=settings,corpus_hash='current',ensure_current=lambda:None)
    options=RetrievalOptions().model_dump()
    identity={'assessment_version':3,'context_format':'source-json-v1','framework':'ragas','version':'0.3.9','corpus':'current','options':options,
        'embedding_config':embedder.identity,'chunking_config':default_chunking_config(options['chunking']),
        'generation_provider':settings.generation_provider,'generation_model':settings.generation_model,
        'generation_prompt_sha256':generation_prompt_identity(),
        'case_id':'q','reference_hash':hashlib.sha256(b'180').hexdigest(),
        'case_set_hash':hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest(),
        'quality_assessment':False,'judge_provider':'ollama','judge_model':'test',
        'precision_prompt_version':4,'precision_prompt_sha256':'53e7c600fb817717e0f57bcbfbabf285b00ec500a83c9af598d43f3bb4148ab4',
        'judge_calibration':{'version':2,'passed':True}}
    row={**options,'case_id':'q','case_kind':'question','identity':identity,
        'judge_calibration_passed':True,'ragas_faithfulness':.8,
        'sample':{'user_input':'Goal?','reference':'180','response':'180','retrieved_contexts':['180']}}
    out=settings.data/'runs/ragas/latest';out.mkdir(parents=True)
    result=out/'results.json';result.write_text(json.dumps([row]))
    assert load_current_ragas(service)==[row]
    row['identity']['generation_prompt_sha256']='different-prompt';result.write_text(json.dumps([row]))
    assert load_current_ragas(service)==[]
    row['identity']['generation_prompt_sha256']=generation_prompt_identity();result.write_text(json.dumps([row]))
    cases[0]['question']='Changed?';path.write_text(json.dumps(cases))
    assert load_current_ragas(service)==[]
    cases[0]['question']='Goal?';path.write_text(json.dumps(cases))
    row['judge_calibration_passed']=False;result.write_text(json.dumps([row]))
    assert load_current_ragas(service)==[]
    row['judge_calibration_passed']=True
    row['identity']['precision_prompt_sha256']='stale'
    result.write_text(json.dumps([row]))
    assert load_current_ragas(service)==[]


def test_missing_calibration_blocks_nonquality_assessment(tmp_path):
    import json
    from campaign_hub.config import Settings
    from campaign_hub.evaluation.ragas_assessment import run_assessment
    settings=Settings(root=tmp_path);(settings.data/'evaluation').mkdir(parents=True)
    (settings.data/'evaluation/questions.json').write_text(json.dumps([
        {'id':'q','kind':'question','split':'held_out','question':'Q','expected_answer':'A'}]))
    def forbidden(*args):raise AssertionError('Uncalibrated judge cannot trigger generation')
    service=SimpleNamespace(settings=settings,answer_question=forbidden)
    assert run_assessment(service,tmp_path/'runs',[RetrievalOptions()],SimpleNamespace(identity={}))==[]
    assert json.loads((tmp_path/'runs/results.json').read_text())==[]


def test_failed_calibration_status_is_saved_and_only_current_status_is_loaded(tmp_path,monkeypatch):
    import json
    from campaign_hub.config import Settings
    from campaign_hub.evaluation.ragas_assessment import run_assessment
    from campaign_hub.ui.current_ragas_results import load_current_calibrations
    settings=Settings(root=tmp_path);(settings.data/'evaluation').mkdir(parents=True)
    case={'id':'q','kind':'question','split':'held_out','question':'Q','expected_answer':'A','expected_sources':['brief']}
    (settings.data/'evaluation/questions.json').write_text(json.dumps([case]))
    monkeypatch.setattr('campaign_hub.embeddings.providers.create_embedder',lambda _:SimpleNamespace(identity={'model':'test'}))
    service=SimpleNamespace(settings=settings,corpus_hash='current',ensure_current=lambda:None)
    identity={'framework':'ragas','version':'0.3.9','assessment_version':3,'context_format':'source-json-v1','judge_provider':'ollama','judge_model':'test',
        'precision_prompt_version':4,'precision_prompt_sha256':'53e7c600fb817717e0f57bcbfbabf285b00ec500a83c9af598d43f3bb4148ab4',
        'quality_assessment':False,'judge_calibration':{'version':2,'passed':False,'controls':[]}}
    out=settings.data/'runs/ragas/latest'
    assert run_assessment(service,out,[RetrievalOptions()],SimpleNamespace(identity=identity))==[]
    statuses=load_current_calibrations(service)
    assert len(statuses)==1 and statuses[0]['calibration']['passed'] is False
    saved=json.loads((out/'calibration-status.json').read_text())
    saved[0]['identity']['precision_prompt_sha256']='old'
    (out/'calibration-status.json').write_text(json.dumps(saved))
    assert load_current_calibrations(service)==[]


def test_current_calibration_failure_is_visible_without_scores(monkeypatch):
    from campaign_hub.ui import current_ragas_results as view
    import streamlit as st
    statuses=[{'identity':{'judge_provider':'ollama','judge_model':'local'},
        'calibration':{'passed':False,'controls':[{'passed':False}]}}]
    monkeypatch.setattr(view,'load_current_calibrations',lambda _:statuses)
    monkeypatch.setattr(view,'load_current_ragas',lambda _:[])
    warnings=[]
    monkeypatch.setattr(st,'subheader',lambda *a,**k:None)
    monkeypatch.setattr(st,'info',lambda *a,**k:None)
    monkeypatch.setattr(st,'warning',lambda text:warnings.append(text))
    view.show_current_ragas(object())
    assert len(warnings)==1 and 'ollama / local' in warnings[0]
    assert 'Metrics from this judge remain unavailable' in warnings[0]


def test_current_judge_contract_rejects_other_framework_versions():
    from campaign_hub.ui.current_ragas_results import _current_judge_contract
    from campaign_hub.evaluation.precision_prompt import PRECISION_PROMPT_SHA256
    identity={'version':'0.3.9','precision_prompt_version':4,'precision_prompt_sha256':PRECISION_PROMPT_SHA256,
        'judge_calibration':{'version':2},'judge_provider':'ollama','judge_model':'local'}
    assert _current_judge_contract(identity)
    assert not _current_judge_contract({**identity,'version':'0.4.0'})
    assert not _current_judge_contract({k:v for k,v in identity.items() if k!='version'})
