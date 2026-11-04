from types import SimpleNamespace
import pytest
from campaign_hub.models import Chunk,SearchHit


def hit(text,section='Document'):
    return SearchHit(chunk=Chunk(chunk_id='brief',text=text,metadata={'section_name':section}),score=.5)


def test_focus_keeps_only_retrieved_goal_section_and_retains_provenance():
    from campaign_hub.retrieval.focus import focus_context
    rows=[hit('## Objectives\nAcquire 180 activations.\n\n## Audience\nLocal households.')]
    result=focus_context('What were the objectives?',rows)
    assert result[0].chunk.text=='Acquire 180 activations.'
    assert result[0].chunk.metadata['parent_chunk_id']=='brief'
    assert result[0].score==.5
    assert focus_context('How did results compare with earlier goals?',rows)==rows
    assert focus_context('What were the goals versus last quarter?',rows)==rows
    assert focus_context('How did the goals track?',rows)==rows
    assert focus_context('How did the goals perform?',rows)==rows
    assert focus_context('What were the objectives?',[hit('No matching section.')])[0].chunk.text=='No matching section.'


def test_focus_preserves_other_explicitly_requested_topics():
    from campaign_hub.retrieval.focus import focus_context
    rows=[hit('## Objectives\nAcquire 180 activations.\n\n## Audience\nLocal households.')]
    for question in ['What were the objectives and audience?', 'What were the goals and budget?',
                     'What were the objectives and eligibility requirements?']:
        assert focus_context(question,rows)==rows


def test_target_gate_does_not_pass_smoke_missing_or_abstained_cases():
    from campaign_hub.evaluation.quality import quality_summary
    good={'case_id':'q1','abstained':False,'error':None,'ragas_faithfulness':1.,
          'ragas_factual_correctness':1.,'passage_relevance_precision':1.,'ragas_context_recall':1.,'judge_calibration_passed':True}
    assert quality_summary([good],['q1','q2'],[])['status']=='incomplete'
    result=quality_summary([good],['q1'],[])
    assert result['status']=='target_met_on_evaluated_set'
    missing={**good,'ragas_faithfulness':None}
    assert quality_summary([missing],['q1'],[])['status']=='incomplete'
    assert quality_summary([{**good,'abstained':True}],['q1'],[])['status']=='below_target'
    assert quality_summary([good],['q1'],['u1'])['status']=='incomplete'
    assert quality_summary([{**good,'judge_calibration_passed':False}],['q1'],[])['status']=='incomplete'
    with pytest.raises(ValueError):quality_summary([good,good],['q1'],[])


def test_passage_fraction_is_distinct_from_ranked_precision_and_partial_failure():
    from campaign_hub.evaluation.quality import passage_precision
    verdicts=[{'verdict':1},{'verdict':0},{'verdict':0}]
    assert passage_precision(verdicts,3)==pytest.approx(1/3)
    assert passage_precision(verdicts,4) is None
    assert passage_precision([],0) is None


def test_judge_controls_detect_reference_copying_instead_of_passage_judgment():
    import asyncio
    from campaign_hub.evaluation.ragas_assessment import judge_controls
    class AlwaysRelevant:
        async def single_turn_ascore(self,sample):return 1.
    result=asyncio.run(judge_controls(AlwaysRelevant(),lambda **x:SimpleNamespace(**x),timeout=1))
    assert result['passed'] is False
    assert [c['expected'] for c in result['controls']]==[1,0,0,0]


def test_calibration_checks_content_despite_matching_source_identity():
    import asyncio,json
    from campaign_hub.evaluation.ragas_assessment import judge_controls
    seen=[]
    class ContentJudge:
        async def single_turn_ascore(self,sample):
            seen.append(sample)
            passage=json.loads(sample.retrieved_contexts[0])
            return float(passage['text'].startswith('Acquire 180'))
    result=asyncio.run(judge_controls(ContentJudge(),lambda **x:SimpleNamespace(**x),timeout=1))
    assert result['passed']
    assert all(json.loads(s.retrieved_contexts[0])['id'].startswith('TX-CHK-001:') for s in seen)
    assert all('TX-CHK-001' in s.user_input for s in seen)


def test_evaluation_key_loader_reads_only_key_and_preserves_environment(tmp_path,monkeypatch):
    from campaign_hub.evaluation.quality import configure_evaluation_key
    monkeypatch.delenv('GROQ_API_KEY',raising=False)
    path=tmp_path/'secrets.toml'
    path.write_text('GROQ_API_KEY="private-test-value"\nCIH_GENERATION_MODEL="do-not-override"\n')
    configure_evaluation_key(path)
    import os
    assert os.environ['GROQ_API_KEY']=='private-test-value'
    assert os.environ.get('CIH_GENERATION_MODEL')!='do-not-override'
    monkeypatch.setenv('GROQ_API_KEY','environment-value')
    configure_evaluation_key(path)
    assert os.environ['GROQ_API_KEY']=='environment-value'


def test_failed_judge_control_prevents_answer_calls(tmp_path):
    import json
    from campaign_hub.config import Settings
    from campaign_hub.models import RetrievalOptions
    from campaign_hub.evaluation.ragas_assessment import run_assessment
    settings=Settings(root=tmp_path);(settings.data/'evaluation').mkdir(parents=True)
    (settings.data/'evaluation/questions.json').write_text(json.dumps([
        {'id':'q1','kind':'question','split':'held_out','question':'Goal?','expected_answer':'180','campaign_id':'C'}]))
    def forbidden(*args):raise AssertionError('No generation calls after judge-control failure')
    service=SimpleNamespace(settings=settings,answer_question=forbidden)
    assessor=SimpleNamespace(identity={'judge_calibration':{'passed':False}})
    assert run_assessment(service,tmp_path/'runs',[RetrievalOptions()],assessor,limit=1,quality=True)==[]
    result=json.loads((tmp_path/'runs/quality-summary.json').read_text())[0]
    assert result['status']=='incomplete'


def test_result_focus_retains_numeric_channel_breakdown():
    from campaign_hub.retrieval.focus import focus_context
    rows=[hit('## KPI Results\nTotal activations: 75.\n\n## Channel Insights\nDisplay reached new households.\n\n## Channel Results\nDirect mail: 45 activations. Display: 30 activations.\n\n## Audience Insights\nLocal households.')]
    selected=focus_context('What were the results and channel findings?',rows)
    assert any('Direct mail: 45' in h.chunk.text for h in selected)
    assert any('Total activations: 75' in h.chunk.text for h in selected)
    assert all('Local households.' not in h.chunk.text for h in selected)


def test_reference_f1_includes_supported_refusals_but_not_missing_judgments():
    from campaign_hub.evaluation.quality import reference_f1_summary
    good={'case_id':'a','judge_calibration_passed':True,'abstained':False,'error':None,'ragas_factual_correctness':1.0}
    refusal={**good,'case_id':'b','abstained':True,'ragas_factual_correctness':None}
    summary=reference_f1_summary([good,refusal],['a','b'])
    assert summary['complete'] and summary['score']==.5 and summary['answered']==1
    assert reference_f1_summary([good],['a','b'])['score'] is None
    assert reference_f1_summary([good,good],['a'])['score'] is None
    assert reference_f1_summary([{**good,'ragas_factual_correctness':None}],['a'])['score'] is None
    assert reference_f1_summary([{**refusal,'error':'failed'}],['b'])['score'] is None
    assert reference_f1_summary([{**good,'judge_calibration_passed':False}],['a'])['score'] is None
