from pathlib import Path
import json,re,hashlib,shutil
root=Path(__file__).resolve().parents[1]
dest=root/'data/supplemental';raw=dest/'ocr-raw';raw.mkdir(exist_ok=True)
# Corrections below were checked against 216-DPI renders of the physical pages.
fixes={
 '2023-69':{'1,588,742':'1,388,742','49%':'4.9%','$29.98':'$29.9B','$24.88':'$24.8B','$25.98':'$25.9B','$1.98':'$1.9B','1.2%':'-1.2%'},
 '2023-70':{'$6.68':'$6.6B','$1.88':'$1.8B','$9.38':'$9.3B','110.867':'110,867','=100':'-100'},
 '2024-100':{'$29.98':'$29.9B','$2.38':'$2.3B','32%':'3.2%','29%':'2.9%'},
 '2024-101':{'$6.48':'$6.4B','$6.68':'$6.6B','$2.08':'$2.0B','$1.68':'$1.6B','$10.98':'$10.9B','$10.18':'$10.1B','~100':'-100'},
 '2024-102':{'142.472':'142,472'},'2024-103':{'(3.373)':'(3,373)'},
}
selected={2023:[69,70,71,72],2024:[100,101,102,103,104]}
records=[];audit=[]
for file in (dest/'ocr-raw').glob('*.json'):
    if file.name=='jobs.json':continue
    job=json.loads(file.read_text(encoding='utf8'));key=file.stem
    source_path=dest/job['source']
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==job['source_sha256'], 'Source changed; repeat visual review'
    # Raw OCR records remain unchanged.
    if job['pdf_page'] not in selected[job['report_year']]:continue
    text=job['text'];changes=[]
    for old,new in fixes.get(key,{}).items():
        assert old in text,(key,old)
        text=text.replace(old,new);changes.append({'ocr':old,'verified':new})
    # Remove scan decorations and audit narrative from the first table page.
    if key in ('2023-69','2024-100'):text='Financial Highlights\n'+text.split('BECU AT A GLANCE',1)[1].strip()
    if key=='2023-71':text=text.replace('Real Estate Held for Sale                                                                    11,445','Real Estate Held for Sale                                                                    11,445                 -')
    if key=='2024-104':text=text.replace('‘','')
    text=re.sub(r'[ \t]{2,}',' | ',text)
    year=job['report_year'];text=f'BECU annual report {year}. Table columns left to right: {year}, {year-1}; % change only where printed. Monetary income, financial position and cooperative equity statement amounts are USD in thousands; financial highlights and lending retain printed B (billions), M (millions), counts and percentages. Cooperative equity rollforward dates are explicitly printed.\n'+text
    job.update(text=text,reviewed=True,review_method='Visual comparison against physical PDF page; OCR character corrections recorded in audit',ocr_raw_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    job.pop('image',None);records.append(job);audit.append({'source':job['source'],'page':job['pdf_page'],'corrections':changes,'reviewed':True})
records.sort(key=lambda r:(r['report_year'],r['pdf_page']))
(dest/'ocr-pages.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf8')
(dest/'ocr-review-audit.json').write_text(json.dumps({'engine':'tesseract.js 7.0.0','render_dpi':216,'raw_pages':19,'reviewed_table_pages':len(records),'scope':'Selected 2023/2024 financial tables only; other raw OCR is excluded from retrieval.','pages':audit},indent=2),encoding='utf8')
print('Reviewed and indexed-eligible pages:',len(records))

import runpy
runpy.run_path(str(root/'scripts/contextualize_becu_ocr.py'))
