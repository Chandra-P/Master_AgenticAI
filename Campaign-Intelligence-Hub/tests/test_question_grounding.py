from types import SimpleNamespace
import pytest


@pytest.mark.parametrize('question,document_type',[
    ('What were the objectives?','brief'),
    ('What was the opening account balance goal?','success_plan'),
    ('What was the acquisition cost goal?','success_plan'),
    ('Did we meet the goals?',None),
    ('How are we tracking toward the goals?',None)])
def test_question_prompt_matches_verbatim_validation(monkeypatch,question,document_type):
    from campaign_hub.reporting.service import CampaignService,Draft
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
    def search(*args):
        searched.append(args)
        return [SearchHit(chunk=chunk,score=1)]
    service=SimpleNamespace(campaigns={'TX-CHK-001':{}},settings=object(),search=search)
    result=CampaignService.answer_question(service,question,'TX-CHK-001',RetrievalOptions())
    assert 'verbatim' in seen['system']
    assert 'do not paraphrase' in seen['system'].lower()
    assert result['accepted_claims']==1
    assert chunk.text in result['answer']
    assert (searched[0][3] if len(searched[0])>3 else None)==document_type
