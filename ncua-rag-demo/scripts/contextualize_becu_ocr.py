from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
path=root/'data/supplemental/ocr-pages.jsonl'
records=[json.loads(l) for l in path.read_text(encoding='utf8').splitlines()]
for r in records:
    year=r['report_year'];number=r['pdf_page'];section='Financial Highlights'
    if number in (71,102):section='Income statement'
    if number in (72,103):section='Financial position'
    if number==104:section='Cooperative equity rollforward'
    period=year if number==104 else year-1
    lines=r['text'].splitlines()[1:]
    if number==104:
        lines=[line for line in lines if 'Fair Value Election for Mortgage Servicing Rights' not in line]
        lines=[line.replace('Cumulative Adjustment for Accounting Change:', 'Cumulative Adjustment for Accounting Change: Fair Value Election for Mortgage Servicing Rights') for line in lines]
    passages=[]
    for line in lines:
        line=line.strip()
        if 'MEMBER LENDING' in line:section='Member lending';continue
        if 'NET PROMOTER SCORE' in line:section='Net Promoter Score';continue
        if 'INCOME FOR THE YEARS' in line:section='Income statement';continue
        if 'FINANCIAL POSITION FOR THE YEARS' in line:section='Financial position';continue
        if line.startswith('COOPERATIVE EQUITY ('):section='Cooperative equity rollforward';continue
        if '|' not in line or not re.search(r'\d',line):continue
        if line.startswith(('DECEMBER 31','2023','2024','*','Scores can')):continue
        if line.startswith('Balance at January 1,'):period=int(re.search(r'20\d{2}',line)[0])
        if section=='Cooperative equity rollforward':
            context=f'{section}; USD in thousands; year {period}. Dates on balance rows are explicit.'
        else:
            units={'Financial Highlights':'Printed units: members and employees are counts; USD B=billions, M=millions; return per member is USD; final column is percent change.','Member lending':'Printed units: count rows are numbers of loans; USD B=billions; final column is percent change.','Net Promoter Score':'Score points, not USD.'}.get(section,'USD in thousands.')
            context=f'{section}; columns left to right: {year}, {year-1}. {units}'
        passages.append({'context':context,'text':line})
        if section=='Cooperative equity rollforward' and line.startswith('Balance at December 31,'):period=int(re.search(r'20\d{2}',line)[0])+1
    r['passages']=passages
path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf8')
auditpath=path.parent/'ocr-review-audit.json';audit=json.loads(auditpath.read_text())
audit['normalization']='Reviewed table rows repeat section, year columns and units. Equity rollforward rows carry period context. Page 104 multiline mortgage servicing rights adjustment label joined with its $16,310 value.'
audit['searchable_row_passages']=sum(len(r['passages']) for r in records)
auditpath.write_text(json.dumps(audit,indent=2),encoding='utf8')
print('Contextualized rows:',audit['searchable_row_passages'])
