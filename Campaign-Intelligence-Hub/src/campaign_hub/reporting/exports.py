"""Portable PDF and editable DrawingML PowerPoint exports from one factual packet."""
from io import BytesIO
from xml.sax.saxutils import escape
import zipfile
import textwrap
from campaign_hub.reporting.client_packet import validate_packet


def _check(packet):
    errors=validate_packet(packet)
    if errors:
        raise ValueError('Report validation failed; not ready: '+'; '.join(errors))


def _citation_text(packet,section):
    cited=packet['sections'][-1]['citations']
    return 'Sources: '+', '.join(f'[{cited.index(c)+1}]' for c in section['citations'])


def export_pdf(packet):
    _check(packet)
    from campaign_hub.reporting.pdf_report import render_pdf
    return render_pdf(packet,_citation_text)


def _paragraph(text,size=2100,color='142B43',bold=False):
    return f'<a:p><a:pPr marL="0" marR="0"/><a:r><a:rPr lang="en-US" sz="{size}" b="{int(bold)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t xml:space="preserve">{escape(text)}</a:t></a:r><a:endParaRPr lang="en-US" sz="{size}"/></a:p>'


def _textbox(ident,name,text,x,y,w,h,size=2100,color='142B43',bold=False):
    paragraphs=''.join(_paragraph(t,size,color,bold) for t in text.split('\n'))
    return f'<p:sp><p:nvSpPr><p:cNvPr id="{ident}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" rIns="0" tIns="0" bIns="0"/><a:lstStyle/>{paragraphs}</p:txBody></p:sp>'


def _slide(title,body,footer,cover=False):
    color='FFFFFF' if cover else '142B43'
    bg='11263D' if cover else 'F4F6F8'
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{bg}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'+_textbox(2,'Title',title,650000,430000,10800000,1050000,3400,color,True)+_textbox(3,'Body',body,650000,1630000,10700000,4200000,2300,color)+_textbox(4,'Citations',footer,650000,6010000,10800000,480000,1100,'80C7C5' if cover else '536778')+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'


def _parts(text,limit=10):
    """Paginate on whole paragraphs; no unsupported condensation or truncation."""
    result=[]; group=[]; count=0
    for para in text.split('\n\n'):
        # Source appendix uses line boundaries as individual paragraphs.
        units=para.split('\n') if '\n' in para else [para]
        for unit in units:
            lines=max(1,len(textwrap.wrap(unit,width=75)))
            if group and count+lines+1>limit:
                result.append('\n\n'.join(group)); group=[]; count=0
            group.append(unit); count+=lines+1
    if group:
        result.append('\n\n'.join(group))
    return result


def export_pptx(packet):
    _check(packet)
    slides=[_slide('Campaign Performance Report',f"{packet['client_name']}\n\n{packet['campaign_name']}\n{packet['period']} | As of {packet['facts']['as_of']}\n\nSYNTHETIC DEMONSTRATION DATA",'Campaign Intelligence Hub | Prepared for analyst review',True)]
    from campaign_hub.reporting.visuals import comparison_panels
    from campaign_hub.reporting.native_charts import chart_frame,chart_xml,workbook
    chart_slides={}
    for section in packet['sections']:
        if section['title']=='Progress Toward Goals':
            for panel in comparison_panels(packet):
                slide=_slide(panel['title'],'',_citation_text(packet,panel)+' | Synthetic demonstration')
                additions=chart_frame()+_textbox(6,'Insight heading','What the data shows',650000,4300000,10700000,300000,1800,'087F80',True)+_textbox(7,'Insight',panel['insight'],650000,4690000,10700000,1120000,1700)
                slides.append(slide.replace('</p:spTree>',additions+'</p:spTree>'))
                chart_slides[len(slides)]=panel
            absent=[r['channel'] for r in packet['facts']['history'] if r['status']!='ok']
            if absent:
                slides.append(_slide('Historical evidence limitations','No compatible same-client history: '+', '.join(absent)+'. No rank is inferred. Industry benchmarks are unavailable.',_citation_text(packet,section)))
            continue
        parts=_parts(section['text'])
        for n,body in enumerate(parts):
            title=section['title']+(f' ({n+1}/{len(parts)})' if len(parts)>1 else '')
            slides.append(_slide(title,body,_citation_text(packet,section)+' | Synthetic demonstration'))
    relns='http://schemas.openxmlformats.org/package/2006/relationships'
    officens='http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    def rels(items):
        return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{relns}">'+''.join(f'<Relationship Id="{i}" Type="{officens+t}" Target="{target}"/>' for i,t,target in items)+'</Relationships>'
    stream=BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        types=[('/ppt/presentation.xml','application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'),
               ('/ppt/slideMasters/slideMaster1.xml','application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'),
               ('/ppt/slideLayouts/slideLayout1.xml','application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
               ('/ppt/theme/theme1.xml','application/vnd.openxmlformats-officedocument.theme+xml')]
        types += [(f'/ppt/slides/slide{i}.xml','application/vnd.openxmlformats-officedocument.presentationml.slide+xml') for i in range(1,len(slides)+1)]
        types += [(f'/ppt/charts/chart{i}.xml','application/vnd.openxmlformats-officedocument.drawingml.chart+xml') for i in chart_slides]
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>'+''.join(f'<Override PartName="{p}" ContentType="{t}"/>' for p,t in types)+'</Types>')
        z.writestr('_rels/.rels',rels([('rId1','officeDocument','ppt/presentation.xml')]))
        z.writestr('ppt/presentation.xml','<?xml version="1.0"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>'+''.join(f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>' for i in range(1,len(slides)+1))+'</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>')
        z.writestr('ppt/_rels/presentation.xml.rels',rels([('rId1','slideMaster','slideMasters/slideMaster1.xml')]+[(f'rId{i+1}','slide',f'slides/slide{i}.xml') for i in range(1,len(slides)+1)]))
        tree='<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree>'
        ns='xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
        z.writestr('ppt/slideMasters/slideMaster1.xml',f'<p:sldMaster {ns}><p:cSld>{tree}</p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>')
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels',rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','theme','../theme/theme1.xml')]))
        z.writestr('ppt/slideLayouts/slideLayout1.xml',f'<p:sldLayout {ns} type="blank" preserve="1"><p:cSld name="Blank">{tree}</p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels',rels([('rId1','slideMaster','../slideMasters/slideMaster1.xml')]))
        palette={'dk1':'11263D','lt1':'FFFFFF','dk2':'536778','lt2':'F4F6F8','accent1':'087F80','accent2':'D99C52','accent3':'648CA6','accent4':'5D7B68','accent5':'815B87','accent6':'C87366','hlink':'087F80','folHlink':'815B87'}
        z.writestr('ppt/theme/theme1.xml','<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Campaign Intelligence"><a:themeElements><a:clrScheme name="Campaign">'+''.join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k,v in palette.items())+'</a:clrScheme><a:fontScheme name="Arial"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Campaign"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')
        for i,slide in enumerate(slides,1):
            z.writestr(f'ppt/slides/slide{i}.xml',slide)
            links=[('rId1','slideLayout','../slideLayouts/slideLayout1.xml')]
            if i in chart_slides:
                panel=chart_slides[i]
                links.append(('rId2','chart',f'../charts/chart{i}.xml'))
                z.writestr(f'ppt/charts/chart{i}.xml',chart_xml(panel))
                z.writestr(f'ppt/embeddings/chart{i}.xlsx',workbook(panel))
                z.writestr(f'ppt/charts/_rels/chart{i}.xml.rels',rels([('rId1','package',f'../embeddings/chart{i}.xlsx')]))
            z.writestr(f'ppt/slides/_rels/slide{i}.xml.rels',rels(links))
    return stream.getvalue()
