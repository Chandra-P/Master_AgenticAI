import asyncio
import os
from types import SimpleNamespace
import pytest


def test_strict_precision_uses_every_passage_and_keeps_ragas_rank_scoring():
    os.environ['RAGAS_DO_NOT_TRACK']='true';pytest.importorskip('ragas')
    from ragas import SingleTurnSample
    from ragas.metrics import LLMContextPrecisionWithReference
    from campaign_hub.evaluation.precision_prompt import create_precision_prompt
    from campaign_hub.evaluation.ragas_assessment import score_sample
    calls=[];settings=[]
    class Model:
        def model_copy(self,update):settings.append(update);return self
        def with_structured_output(self,schema,method):
            assert method=='json_schema'
            class Chain:
                async def ainvoke(self,prompt,config):
                    calls.append(prompt)
                    return schema(reason='Relevant' if 'UNIQUE_TARGET' in prompt else 'Unrelated',
                        verdict=int('UNIQUE_TARGET' in prompt))
            return Chain()
    prompt=create_precision_prompt(Model(),'ollama')
    metric=LLMContextPrecisionWithReference(llm=SimpleNamespace(),context_precision_prompt=prompt)
    sample={'user_input':'What is the goal?','reference':'180 activations.','response':'180 activations.',
        'retrieved_contexts':['UNIQUE_NOISE','UNIQUE_TARGET']}
    result=asyncio.run(score_sample(sample,{'ragas_context_precision':metric},SingleTurnSample))
    assert result['ragas_context_precision']==pytest.approx(.5),result
    assert len(calls)==2 and 'UNIQUE_NOISE' in calls[0] and 'UNIQUE_TARGET' in calls[1]
    assert settings==[{'num_predict':256}]
    assert len(prompt.to_string())<3000
    with pytest.raises(ValueError):prompt.output_model(reason='Invalid binary value',verdict=2)
