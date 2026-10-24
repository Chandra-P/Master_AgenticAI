import json
import pytest
from langchain_core.documents import Document

def page(text,year=2024):
    return {'source':f'5536-annual-{year}.pdf','source_url':'https://www.navyfederal.org/report.pdf','institution':'NAVY FEDERAL CREDIT UNION','charter':'5536','report_year':year,'pdf_page':3,'text':text}

def test_membership_row_keeps_years_counts_units_and_pdf_provenance():
    from pipeline.extract import extract_membership_table
    docs=extract_membership_table(page('Financial Summary\nAs of December 31\n(dollars in millions) 2023 2024\nMembers 13,342,112 14,266,170'))
    assert len(docs)==1
    assert 'Dec-2023: 13,342,112' in docs[0].page_content
    assert 'Dec-2024: 14,266,170' in docs[0].page_content
    assert 'Units: individual members' in docs[0].page_content
    assert docs[0].metadata['pdf_page']==3
    assert docs[0].metadata['source_type']=='institution_annual_report'

def test_membership_column_order_is_preserved_including_descending_years():
    from pipeline.extract import extract_membership_table
    doc=extract_membership_table(page('Financial Summary\nAs of December 31\n2024 2023\nMembership 14266170 13342112'))[0]
    assert 'Dec-2024: 14,266,170' in doc.page_content
    assert 'Dec-2023: 13,342,112' in doc.page_content

@pytest.mark.parametrize('text',[
    'Financial Summary\nMembers 13,342,112 14,266,170',
    'Financial Summary\n2022 2023 2024\nMembers 13,342,112 14,266,170',
    'Financial Summary\n2023 2024\nMembers’ Equity 13,342,112 14,266,170',
    'Financial Summary\n2023 2024\nMembers 13,342,112 14,26,170',
    'Members 13,342,112 14,266,170\n2023 2024',
])
def test_ambiguous_or_non_membership_rows_are_not_reconstructed(text):
    from pipeline.extract import extract_membership_table
    assert extract_membership_table(page(text.replace('Financial Summary','Financial Summary\nAs of December 31')))==[]

def test_loader_appends_table_rows_without_reordering_existing_passages(tmp_path):
    from pipeline.extract import load_supplemental
    folder=tmp_path/'supplemental';folder.mkdir()
    p=page('Financial Summary\nAs of December 31\n2023 2024\nMembers 13,342,112 14,266,170')
    p['source_type']='institution_annual_report';p['empty_text']=False
    (folder/'pages.jsonl').write_text(json.dumps(p)+'\n')
    docs=load_supplemental(tmp_path)
    assert docs[0].metadata['row']=='Annual report passage'
    assert docs[-1].metadata['row']=='Members (membership count)'

def test_incremental_index_embeds_only_added_rows(tmp_path):
    from pipeline.index import Store
    from langchain_core.embeddings import Embeddings
    class Counting(Embeddings):
        identity='counting-membership-test'
        def __init__(self):self.calls=[]
        def embed_documents(self,texts):self.calls.extend(texts);return [[1.,0.,0.] for _ in texts]
        def embed_query(self,text):return [1.,0.,0.]
    encoder=Counting();store=Store(tmp_path,'fixed',encoder)
    first=Document(id='first',page_content='First report',metadata={'source':'first'})
    added=Document(id='new',page_content='Exact membership row',metadata={'source':'new'})
    store.build([first]);encoder.calls.clear();store.build([first,added])
    assert encoder.calls==['Exact membership row']
    changed=Document(id='new',page_content='Corrected membership row',metadata={'source':'new','corrected':True})
    encoder.calls.clear();store.build([first,changed])
    assert encoder.calls==['Corrected membership row']
    assert store.collection.get(ids=['new'])['metadatas'][0]['corrected'] is True
