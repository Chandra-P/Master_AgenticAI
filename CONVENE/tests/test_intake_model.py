from types import SimpleNamespace

import pytest

from convene.domain import EventBriefVersion
from convene.intake import BriefAnswers, ExtractedAnswer


def test_extractor_uses_structured_unstored_bounded_call():
    from convene.intake_model import OpenAIIntakeExtractor
    calls=[]
    class Client:
        def __init__(self,**kwargs):calls.append(kwargs)
        def __enter__(self):return self
        def __exit__(self,*args):pass
        @property
        def responses(self):return self
        def parse(self,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_parsed=ExtractedAnswer(
                answers=BriefAnswers(occasion='birthday'),evidence='birthday'))
    result=OpenAIIntakeExtractor(api_key='test-only',client_factory=Client)(
        'birthday',EventBriefVersion(),[])
    assert result.answers.occasion=='birthday'
    assert calls[0]['timeout']==25 and calls[0]['max_retries']==0
    assert calls[1]['store'] is False and 'tools' not in calls[1]
    assert calls[1]['text_format'] is ExtractedAnswer


def test_refusal_has_actionable_error_without_invented_answer():
    from convene.intake_model import OpenAIIntakeExtractor
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        @property
        def responses(self):return self
        def parse(self,**kwargs):return SimpleNamespace(output_parsed=None)
    with pytest.raises(ValueError,match='rephrase'):
        OpenAIIntakeExtractor(api_key='test-only',client_factory=Client)('hi',EventBriefVersion(),[])
