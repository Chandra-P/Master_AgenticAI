from types import SimpleNamespace


def test_question_prompt_matches_verbatim_validation(monkeypatch):
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
    service=SimpleNamespace(campaigns={'TX-CHK-001':{}},settings=object(),search=lambda *args:[SearchHit(chunk=chunk,score=1)])
    result=CampaignService.answer_question(service,'What were the objectives?','TX-CHK-001',RetrievalOptions())
    assert 'verbatim' in seen['system']
    assert 'do not paraphrase' in seen['system'].lower()
    assert result['accepted_claims']==1
    assert chunk.text in result['answer']
