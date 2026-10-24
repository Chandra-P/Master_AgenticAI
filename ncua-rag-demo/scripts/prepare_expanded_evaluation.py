from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1]
dest=root/'evaluation/expanded';dest.mkdir(exist_ok=True)
cases=json.loads((root/'evaluation/questions.json').read_text())
for case in cases:case['domain']='ncua';case['gold_units']=[{'key':key,'kind':'row','source':key.split('|')[0],'row':key.split('|')[1]} for key in case['relevant']]
pages=[json.loads(line) for line in (root/'data/supplemental/pages.jsonl').read_text(encoding='utf8').splitlines()]
def compact(text):return re.sub(r'[\s,$]','',text.casefold())
def add(number,question,charter,year,page,anchors):
    source=f'{charter}-annual-{year}.pdf'
    text=next(p['text'] for p in pages if p['source']==source and p['pdf_page']==page)
    for anchor in anchors:assert compact(anchor) in compact(text),(source,page,anchor)
    units=[{'key':f'{source}|page-{page}|{anchor}','kind':'pdf_anchor','source':source,'page':page,'anchor':anchor} for anchor in anchors]
    cases.append({'id':f'A{number:02}','domain':'annual','question':question,'filters':{'charter':charter,'year_'+str(year):True},'gold_units':units,'expected':'source_evidence'})
for number,(year,page,count) in enumerate([(2021,3,'11,133,370'),(2022,3,'12,322,979'),(2023,3,'13,342,112'),(2024,3,'14,266,170'),(2025,5,'15,139,001')],1):
    add(number,f'What exact year-end membership count appears in Navy Federal\'s {year} annual report financial summary?','5536',year,page,[count])
add(6,'How many Navy Federal members used digital channels in 2021, and what share of membership did they represent according to its annual report?','5536',2021,7,['8.4 million','75%'])
add(7,'How many new members did Navy Federal welcome in 2022 and what membership growth percentage did its annual report report?','5536',2022,5,['1.2 million','10.7%'])
add(8,'In its 2023 annual report, how many Navy Federal members used digital banking, how many times did they use it, and what share of membership was represented?','5536',2023,7,['10 million','2 billion','78%'])
add(9,'According to its 2024 annual report, how many new branches did Navy Federal open for members and how large did its branch network become?','5536',2024,6,['12 new branches','366 locations'])
add(10,'What membership expansion percentage and membership milestone did Navy Federal describe in its 2025 annual report?','5536',2025,4,['6.1%','15 million'])
add(11,'What membership growth percentage and approximate total membership did BECU report in its 2021 annual report?','62604',2021,9,['4.5%','1.3 million'])
add(12,'How many members joined BECU online in 2021 and what growth percentage did its annual report give for that channel?','62604',2021,9,['17,600','21.2%'])
add(13,'In BECU\'s 2021 annual report, how many members benefited from its Reprice Program and how much did they save?','62604',2021,16,['48,000','2.2 million'])
add(14,'What approximate total membership and membership growth percentage did BECU report in its 2022 annual report?','62604',2022,11,['1.4 million','3.6%'])
add(15,'How many new BECU members, digital-channel joiners and new business members did its 2022 annual report describe?','62604',2022,11,['108,200','16,000','10,700'])
add(16,'How much value did BECU return to its members in 2022, what was the average benefit and how much did it grow according to the annual report?','62604',2022,20,['362.3 million','265','8%'])
add(17,'What total membership and new-member count did BECU report at the end of 2025 in its annual report?','62604',2025,5,['1,558,284','112,029'])
add(18,'How many members received Financial Health Checks and how many people attended financial classes according to BECU\'s 2025 annual report?','62604',2025,7,['1,258','5,000'])
add(19,'In BECU\'s 2025 annual report, how many members used Envelopes, how many goals did they set, and how much did those goals total?','62604',2025,7,['31,882','79,239','76 million'])
add(20,'What total value and average individual benefit did BECU return to its members according to its 2025 annual report?','62604',2025,5,['425.7 million','276'])
for i,charter,year,q,reason in [(21,'62604',2023,'How many members did BECU have in 2023 according to its annual report?','PDF has no extractable text; OCR is not implemented.'),(22,'62604',2024,'How many members did BECU have in 2024 according to its annual report?','Extracted PDF text is mostly captions and contains no membership count.'),(23,'67955',2025,'How many members did Alliant have in its 2025 annual report?','No Alliant annual report in corpus.')]:
    cases.append({'id':f'A{i:02}','domain':'annual','question':q,'filters':{'charter':charter,'year_'+str(year):True},'gold_units':[],'expected':'abstain','reason':reason})
alternatives={('A07','1.2 million'):[5,2],('A10','15 million'):[4,3],('A11','4.5%'):[9,3],('A11','1.3 million'):[9,3],('A12','17,600'):[9,3],('A14','1.4 million'):[11,3],('A14','3.6%'):[11,3],('A17','1,558,284'):[5,38],('A20','276'):[5,38],('A20','425.7 million'):[5,38]}
for case in cases:
    for unit in case['gold_units']:
        if unit['kind']=='pdf_anchor':unit['accepted_pages']=alternatives.get((case['id'],unit['anchor']),[unit['page']])
        if case['id']=='A20' and unit.get('anchor')=='425.7 million':unit['anchor_variants']=['425.7 million','425.7M']
payload={'cases':cases,'label_method':'Original 15 row-labeled NCUA questions plus 20 fact-labeled annual-report questions and 3 annual coverage negatives. Annual anchors and equivalent pages verified against physical PDF text before the final retrieval run. No tuning or result-based query selection. PDF facts can share a passage; all supported units count toward recall. Version 2 corrects equivalent-page labels and numeric boundaries before any scores were inspected.','scope':'Retrieval, not generated-answer accuracy. Annual subset deliberately targets membership and member services, not all annual-report content.'}
if (dest/'questions.json').exists() and not (dest/'questions-v1.json').exists():(dest/'questions-v1.json').write_bytes((dest/'questions.json').read_bytes())
text=json.dumps(payload,indent=2);(dest/'questions.json').write_text(text,encoding='utf8')
print('Frozen',len(cases),'questions; label SHA256',hashlib.sha256((dest/'questions.json').read_bytes()).hexdigest())
