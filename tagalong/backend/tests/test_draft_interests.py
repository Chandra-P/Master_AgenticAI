import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from tagalong.coordination_ai import CoordinationGraph,response_schema
from tagalong.coordination_models import PlanDraft


def legacy_draft():
    return {'title':'Friends weekend','type':'trip','location':'Austin','start':None,'end':None,'participant_count':4,'suggested_tasks':[],'suggested_itinerary':[],'suggested_budget':{'amount':None,'basis':'unknown','currency':'','notes':''},'open_questions':['Which dates?']}


def test_legacy_drafts_get_independent_empty_starter_interests():
    first=PlanDraft.model_validate(legacy_draft())
    second=PlanDraft.model_validate(legacy_draft())
    assert first.model_dump()['suggested_interests']==[]
    assert first.interest_reason==''
    first.suggested_interests.append('Food')
    assert second.suggested_interests==[]


@pytest.mark.parametrize('fields',[
    {'suggested_interests':['Shopping']},
    {'suggested_interests':['Food','Outdoors','Music','Arts','Relaxed']},
    {'interest_reason':'x'*501},
])
def test_starter_interests_reject_unknown_labels_and_oversized_output(fields):
    with pytest.raises(ValidationError):PlanDraft.model_validate({**legacy_draft(),**fields})


def test_starter_interests_accept_all_supported_labels():
    for interest in ('Food','Outdoors','Music','Arts','Nightlife','Relaxed'):
        result=PlanDraft.model_validate({**legacy_draft(),'suggested_interests':[interest],'interest_reason':'Starter suggestion for review.'})
        assert result.suggested_interests==[interest]


def test_provider_schema_requires_defaulted_interests_without_defaults():
    schema=response_schema(PlanDraft)
    assert {'suggested_interests','interest_reason'}<=set(schema['required'])
    assert schema['properties']['suggested_interests']['items']['enum']==['Food','Outdoors','Music','Arts','Nightlife','Relaxed']
    assert 'default' not in json.dumps(schema)
    assert schema['additionalProperties'] is False


def test_generate_requests_reviewable_starters_in_one_call_and_accepts_legacy_output():
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(legacy_draft()))
    provider=SimpleNamespace(model='test-model',client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    result=CoordinationGraph(provider).generate_plan('Plan a fun weekend','2027-05-01')
    assert result['suggested_interests']==[] and result['interest_reason']==''
    assert len(calls)==1
    request=calls[0]
    assert request['store'] is False
    assert request['text']['format']['strict'] is True
    assert json.loads(request['input'])=={'request':'Plan a fun weekend','local_reference_date':'2027-05-01'}
    assert 'balanced starter mix' in request['instructions']
    assert 'not confirmed group preferences' in request['instructions']
    assert 'untrusted data' in request['instructions']
