import json
from datetime import date
import pytest


def test_channel_attribution_boundaries():
    from campaign_hub.reporting.attribution import attributable
    anchor=date(2026,1,1)
    assert attributable('direct_mail',anchor,date(2026,3,2))
    assert not attributable('direct_mail',anchor,date(2026,3,3))
    assert attributable('display',anchor,date(2026,1,31))
    assert not attributable('display',anchor,date(2026,2,1))
    assert not attributable('display',anchor,date(2025,12,31))
    with pytest.raises(ValueError):
        attributable('email',anchor,anchor)


def test_only_direct_mail_and_display_with_traceable_windows(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    manifest=generate_corpus(tmp_path)
    for record in manifest['campaigns']:
        assert set(record['channel_results'])=={'direct_mail','display'}
        assert record['channel_results']['direct_mail']['window_days']==60
        assert record['channel_results']['display']['window_days']==30
        assert record['channel_results']['display']['anchor']=='exposure_date'
        assert sum(s['activations'] for s in record['channel_results'].values())==record['actual']
        assert sum(s['spend'] for s in record['channel_results'].values())==record['spend']
    corpus='\n'.join((tmp_path/d['source_path']).read_text() for d in manifest['documents'])
    assert 'paid search' not in corpus.lower()
    assert 'email' not in corpus.lower()
    assert 'last eligible click' not in corpus.lower()
    assert len(manifest['documents'])==110
    assert len(json.loads((tmp_path/'evaluation/questions.json').read_text()))==30


def test_historical_comparison_uses_compatible_earlier_mature_peers():
    from campaign_hub.reporting.benchmark import compare_campaign
    def campaign(cid,year,rate,cost,window=60,mature=True,kind='Checking'):
        return {'campaign_id':cid,'campaign_type':kind,'period':f'{year}-Q2','year':year,
            'channel_results':{'direct_mail':{'window_days':window,'anchor':'mail_drop_date','exposure_unit':'mailed_households',
                'mature':mature,'activations':rate,'exposures':1000,'spend':rate*cost}}}
    current=campaign('CURRENT',2026,20,100)
    peers=[campaign('LOW',2024,10,120),campaign('HIGH',2025,30,80),
           campaign('FUTURE',2027,40,50),campaign('WRONG_WINDOW',2025,40,50,30),
           campaign('IMMATURE',2025,40,50,mature=False),campaign('OTHER',2025,40,50,kind='Mortgage')]
    result=compare_campaign(current,peers,'direct_mail')
    assert result['peer_ids']==['LOW','HIGH']
    assert result['metrics']['activation_rate']['rank']==2
    assert result['metrics']['activation_rate']['total']==3
    assert result['metrics']['activation_rate']['peer_median']==pytest.approx(.02)
    assert result['metrics']['cost_per_activation']['rank']==2
    assert result['metrics']['cost_per_activation']['peer_median']==100
    assert result['metrics']['cost_per_activation']['position']=='at peer median'
    assert compare_campaign(current,[],'direct_mail')['status']=='insufficient_peers'


def test_benchmark_ties_are_not_misrepresented():
    from campaign_hub.reporting.benchmark import percentile
    assert percentile(2,[1,2,3],higher_is_better=True)==50
    assert percentile(2,[1,2,3],higher_is_better=False)==50
    assert percentile(1,[2,3],higher_is_better=False)==100


def test_zero_conversion_peer_counts_for_rate_but_not_cost():
    from campaign_hub.reporting.benchmark import compare_campaign
    def record(cid,period,activations):
        return {'campaign_id':cid,'campaign_type':'Checking','period':period,'channel_results':{'direct_mail':{
            'window_days':60,'anchor':'mail_drop_date','exposure_unit':'mailed_households','mature':True,
            'exposures':1000,'activations':activations,'spend':1000}}}
    result=compare_campaign(record('A','2026-Q2',10),[record('ZERO','2025-Q2',0)],'direct_mail')
    assert result['metrics']['activation_rate']['peer_median']==0
    assert result['metrics']['activation_rate']['rank']==1
    assert 'cost_per_activation' not in result['metrics']


def test_benchmark_reads_retrieved_evidence_not_manifest_actuals(tmp_path,monkeypatch):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.reporting.service import CampaignService
    from campaign_hub.config import Settings
    from campaign_hub.models import Chunk,SearchHit,RetrievalOptions
    generate_corpus(tmp_path/'data')
    service=CampaignService(Settings(root=tmp_path))
    service.campaigns['TX-CHK-001']['channel_results']['direct_mail']['activations']=999999
    def search(query,cid,options,document_type=None):
        meta=service.campaigns[cid]
        count=20 if cid=='TX-CHK-001' else 10
        year=meta['year']
        text=f'| direct_mail | {count} | 1000 | 2000 | 60 | mail_drop_date | {year}-04-01 | {year}-06-30 | mailed_households | true |'
        c=Chunk(chunk_id=cid,text=text,metadata={'campaign_id':cid,'period':meta['period'],'section_name':'Channel Results'})
        return [SearchHit(chunk=c,score=.9)]
    monkeypatch.setattr(service,'search',search)
    result=service.compare_with_history('TX-CHK-001',RetrievalOptions())
    dm=next(c for c in result['comparisons'] if c['channel']=='direct_mail')
    assert dm['metrics']['activation_rate']['current']==.02
    assert result['evidence']


def test_cost_small_sample_uses_defined_cost_peers_not_whole_cohort():
    from campaign_hub.reporting.benchmark import compare_campaign
    def record(cid,period,activations):
        return {'campaign_id':cid,'campaign_type':'Checking','period':period,'channel_results':{'direct_mail':{
            'window_days':60,'anchor':'mail_drop_date','exposure_unit':'mailed_households','mature':True,
            'exposures':1000,'activations':activations,'spend':1000}}}
    peers=[record(f'P{i}','2025-Q2',10 if i==4 else 0) for i in range(5)]
    result=compare_campaign(record('CURRENT','2026-Q2',20),peers,'direct_mail')
    assert result['peer_count']==5 and not result['small_sample']
    cost=result['metrics']['cost_per_activation']
    assert cost['peer_count']==1 and cost['excluded_undefined_cost_peers']==4
    assert cost['small_sample'] is True
