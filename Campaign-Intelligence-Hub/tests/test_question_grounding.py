from types import SimpleNamespace
import pytest


@pytest.mark.parametrize('question,document_type',[
    ('What were the objectives?','brief'),
    ('What was the opening account balance goal?','success_plan'),
    ('What was the acquisition cost goal?','success_plan'),
    ('Did we meet the goals?',None),
    ('How are we tracking toward the goals?',None)])
def test_question_prompt_matches_verbatim_validation(monkeypatch,question,document_type):
    from campaign_hub.rag.grounding import Draft,question_plan
    from campaign_hub.rag.service import RAGService
    from campaign_hub.models import Chunk,SearchHit,RetrievalOptions,EvidenceClaim
    import campaign_hub.generation.providers as providers
    chunk=Chunk(chunk_id='brief-objectives',text='Acquire 180 verified product activations.',metadata={})
    seen={}
    class Generator:
        def generate_json(self,system,prompt,schema):
            seen['system']=system
            return Draft(claims=[EvidenceClaim(text=chunk.text,citations=[chunk.chunk_id])])
    monkeypatch.setattr(providers,'create_generator',lambda settings:Generator())
    searched=[]
    def analyze(*args,**kwargs):
        searched.append(question_plan(question,RetrievalOptions())[0])
        return {"hits":[SearchHit(chunk=chunk,score=1).model_dump()]}
    service=SimpleNamespace(campaigns={'TX-CHK-001':{}},settings=object(),analyze_query=analyze)
    result=RAGService.answer_question(service,question,'TX-CHK-001',RetrievalOptions())
    assert 'verbatim' in seen['system']
    assert 'do not paraphrase' in seen['system'].lower()
    assert result['accepted_claims']==1
    assert chunk.text in result['answer']
    assert searched[0]==document_type


def test_missing_citation_recovered_only_for_unique_exact_retrieved_quote():
    from campaign_hub.rag.grounding import resolve_claim
    from campaign_hub.models import Chunk,EvidenceClaim
    evidence={'one':Chunk(chunk_id='one',text='The retention window is seven days.',metadata={}),
              'two':Chunk(chunk_id='two',text='The review requires approval.',metadata={})}
    original=EvidenceClaim(text='The retention window is seven days.',citations=[])
    recovered=resolve_claim(original,evidence)
    assert recovered.citations==['one']
    assert original.citations==[]
    assert resolve_claim(EvidenceClaim(text='Invented profit.',citations=[]),evidence) is None
    assert resolve_claim(EvidenceClaim(text=original.text,citations=['unknown']),evidence) is None
    assert resolve_claim(EvidenceClaim(text=original.text,citations=['two']),evidence) is None
    assert resolve_claim(EvidenceClaim(text=' ',citations=[]),evidence) is None
    evidence['duplicate']=evidence['one'].model_copy(update={'chunk_id':'duplicate'})
    assert resolve_claim(original,evidence) is None
    valid=EvidenceClaim(text=original.text,citations=['one'])
    assert resolve_claim(valid,evidence)==valid


def test_grounded_answer_attaches_recovered_source_id(monkeypatch):
    from campaign_hub.rag.grounding import Draft,grounded_answer
    from campaign_hub.models import Chunk,SearchHit,EvidenceClaim
    import campaign_hub.generation.providers as providers
    text='A fresh review is required before reuse.'
    class Generator:
        def generate_json(self,*args):return Draft(claims=[EvidenceClaim(text=text,citations=[])])
    monkeypatch.setattr(providers,'create_generator',lambda _:Generator())
    hit=SearchHit(chunk=Chunk(chunk_id='real-source',text=text,metadata={}),score=1)
    result=grounded_answer(object(),'What is required before reuse?',[hit])
    assert result['accepted_claims']==1
    assert result['claims'][0]['citations']==['real-source']
    assert result['answer']==text+' [real-source]'
