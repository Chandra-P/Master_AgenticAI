"""Optional framework integration: known judge verdicts, not claimed model quality."""
import asyncio
import json
import os
import pytest


def test_actual_ragas_computes_claim_support_rank_precision_and_reference_recall():
    os.environ['RAGAS_DO_NOT_TRACK']='true'
    pytest.importorskip('ragas')
    from ragas import SingleTurnSample
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness,LLMContextPrecisionWithReference,LLMContextRecall
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from campaign_hub.evaluation.ragas_assessment import score_sample
    judgments=[
        {'statements':['The goal is 180 activations.','The campaign earned profit.']},
        {'statements':[{'statement':'The goal is 180 activations.','reason':'Present','verdict':1},
                       {'statement':'The campaign earned profit.','reason':'Not measured','verdict':0}]},
        {'reason':'Irrelevant passage','verdict':0},
        {'reason':'Contains the target','verdict':1},
        {'classifications':[{'statement':'The goal is 180 activations.','reason':'Present','attributed':1},
                            {'statement':'The window is 60 days.','reason':'Absent','attributed':0}]}]
    wrapper=LangchainLLMWrapper(FakeListChatModel(responses=[json.dumps(j) for j in judgments]))
    metrics={'ragas_faithfulness':Faithfulness(llm=wrapper),
             'ragas_context_precision':LLMContextPrecisionWithReference(llm=wrapper),
             'ragas_context_recall':LLMContextRecall(llm=wrapper)}
    sample={'user_input':'What is the goal and attribution window?',
        'response':'The goal is 180 activations. The campaign earned profit.',
        'reference':'The goal is 180 activations. The window is 60 days.',
        'retrieved_contexts':['The guide covers reporting styles.','The goal is 180 activations.']}
    result=asyncio.run(score_sample(sample,metrics,SingleTurnSample))
    assert not result['metric_errors'],result
    assert result['ragas_faithfulness']==pytest.approx(.5)
    assert result['ragas_context_precision']==pytest.approx(.5)
    assert result['ragas_context_recall']==pytest.approx(.5)


def test_local_judge_requests_json_for_the_ragas_json_contract():
    os.environ['RAGAS_DO_NOT_TRACK']='true'
    pytest.importorskip('ragas')
    from campaign_hub.config import Settings
    from campaign_hub.evaluation.ragas_assessment import RagasAssessor
    with RagasAssessor(Settings(generation_provider='ollama')) as assessor:
        assert assessor.metrics['ragas_faithfulness'].llm.langchain_llm.format=='json'
        assert assessor.identity['judge_json_mode'] is True
