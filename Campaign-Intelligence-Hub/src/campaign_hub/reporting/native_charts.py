"""Editable PowerPoint bar charts with matching embedded source workbooks."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from xml.sax.saxutils import escape

REL='http://schemas.openxmlformats.org/package/2006/relationships'
OFFICE='http://schemas.openxmlformats.org/officeDocument/2006/relationships/'


def workbook(panel):
    stream=BytesIO()
    with ZipFile(stream,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels',f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{OFFICE}officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="{OFFICE[:-1]}"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{OFFICE}worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        rows=['<row r="1"><c r="A1" t="inlineStr"><is><t>Category</t></is></c><c r="B1" t="inlineStr"><is><t>Value</t></is></c></row>']
        for i,(label,value) in enumerate(zip(panel['labels'],panel['values']),2):
            rows.append(f'<row r="{i}"><c r="A{i}" t="inlineStr"><is><t>{escape(label)}</t></is></c><c r="B{i}"><v>{value}</v></c></row>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(rows)+'</sheetData></worksheet>')
    return stream.getvalue()


def chart_xml(panel):
    n=len(panel['values']); end=n+1
    fmt='0.00%' if panel['unit']=='percent' else '$#,##0.00' if panel['unit']=='USD' else '#,##0'
    labels=''.join(f'<c:pt idx="{i}"><c:v>{escape(label)}</c:v></c:pt>' for i,label in enumerate(panel['labels']))
    values=''.join(f'<c:pt idx="{i}"><c:v>{value}</c:v></c:pt>' for i,value in enumerate(panel['values']))
    points=''.join(f'<c:dPt><c:idx val="{i}"/><c:spPr><a:solidFill><a:srgbClr val="'+('087F80' if i in panel['highlights'] else '8BA0AF')+'"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr></c:dPt>' for i in range(n))
    title={'USD':'USD','percent':'Activation rate (%)','accounts':'Attributed accounts'}[panel['unit']]
    return f'''<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="{OFFICE[:-1]}">
<c:date1904 val="0"/><c:lang val="en-US"/><c:chart><c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="1400"/><a:t>{title}</a:t></a:r></a:p></c:rich></c:tx><c:overlay val="0"/></c:title><c:plotArea><c:layout/><c:barChart><c:barDir val="bar"/><c:grouping val="clustered"/><c:varyColors val="1"/>
<c:ser><c:idx val="0"/><c:order val="0"/><c:tx><c:strRef><c:f>Data!$B$1</c:f><c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Value</c:v></c:pt></c:strCache></c:strRef></c:tx><c:spPr><a:solidFill><a:srgbClr val="087F80"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr><c:invertIfNegative val="0"/>{points}
<c:cat><c:strRef><c:f>Data!$A$2:$A${end}</c:f><c:strCache><c:ptCount val="{n}"/>{labels}</c:strCache></c:strRef></c:cat><c:val><c:numRef><c:f>Data!$B$2:$B${end}</c:f><c:numCache><c:formatCode>{fmt}</c:formatCode><c:ptCount val="{n}"/>{values}</c:numCache></c:numRef></c:val></c:ser>
<c:dLbls><c:numFmt formatCode="{fmt}" sourceLinked="0"/><c:dLblPos val="outEnd"/><c:showLegendKey val="0"/><c:showVal val="1"/><c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="0"/></c:dLbls><c:gapWidth val="85"/><c:axId val="1"/><c:axId val="2"/></c:barChart>
<c:catAx><c:axId val="1"/><c:scaling><c:orientation val="maxMin"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:tickLblPos val="nextTo"/><c:crossAx val="2"/><c:crossesAt val="0"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/></c:catAx>
<c:valAx><c:axId val="2"/><c:scaling><c:orientation val="minMax"/><c:max val="{max(panel['values'])*1.25 or 1}"/><c:min val="0"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:majorGridlines><c:spPr><a:ln w="6000"><a:solidFill><a:srgbClr val="E0E7EC"/></a:solidFill></a:ln></c:spPr></c:majorGridlines><c:numFmt formatCode="{fmt}" sourceLinked="0"/><c:tickLblPos val="nextTo"/><c:crossAx val="1"/><c:crosses val="max"/><c:crossBetween val="between"/></c:valAx></c:plotArea><c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>
<c:spPr><a:solidFill><a:srgbClr val="F4F6F8"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr><c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1300"><a:solidFill><a:srgbClr val="142B43"/></a:solidFill><a:latin typeface="Arial"/></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr><c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>'''


def chart_frame():
    return f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="5" name="Editable comparison chart"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="650000" y="1400000"/><a:ext cx="10700000" cy="2800000"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:r="{OFFICE[:-1]}" r:id="rId2"/></a:graphicData></a:graphic></p:graphicFrame>'
