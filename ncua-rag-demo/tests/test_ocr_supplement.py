import json
from pipeline.extract import load_supplemental

def record(**changes):
    return dict(source='62604-annual-2023.pdf',source_url='https://www.becu.org/report.pdf',institution='BOEING EMPLOYEES',charter='62604',report_year=2023,pdf_page=69,text='Members 1,445,000',**changes)

def test_verified_ocr_is_appended_with_method_and_provenance(tmp_path):
    folder=tmp_path/'supplemental';folder.mkdir()
    (folder/'pages.jsonl').write_text('')
    (folder/'ocr-pages.jsonl').write_text(json.dumps(record(reviewed=True,engine='tesseract.js 7.0.0',source_sha256='abc'))+'\n')
    docs=load_supplemental(tmp_path)
    assert len(docs)==1
    assert '1,445,000' in docs[0].page_content
    assert docs[0].metadata['pdf_page']==69
    assert docs[0].metadata['extraction_method']=='OCR: tesseract.js 7.0.0'
    assert docs[0].metadata['source_sha256']=='abc'
    assert 'OCR' in docs[0].metadata['warning']

def test_unreviewed_ocr_is_not_searchable(tmp_path):
    folder=tmp_path/'supplemental';folder.mkdir()
    (folder/'pages.jsonl').write_text('')
    (folder/'ocr-pages.jsonl').write_text(json.dumps(record(reviewed=False,engine='test'))+'\n')
    assert load_supplemental(tmp_path)==[]

def test_reviewed_rows_repeat_year_and_unit_context(tmp_path):
    folder=tmp_path/'supplemental';folder.mkdir()
    (folder/'pages.jsonl').write_text('')
    p=record(reviewed=True,engine='test',passages=[{'context':'Financial position; columns 2023, 2022; USD in thousands','text':'Loans, Net | 18,409,695 | 16,298,351'},{'context':'Income; columns 2023, 2022; USD in thousands','text':'Net Income | 211,302 | 105,935'}])
    (folder/'ocr-pages.jsonl').write_text(json.dumps(p)+'\n')
    docs=load_supplemental(tmp_path)
    assert len(docs)==2
    assert all('2023, 2022; USD in thousands' in d.page_content for d in docs)
    assert 'Loans, Net' in docs[0].page_content and 'Net Income' in docs[1].page_content
