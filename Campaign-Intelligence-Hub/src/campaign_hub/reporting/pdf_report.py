"""Chart-led PDF layout with adjacent, deterministic findings and citations."""
from io import BytesIO
from xml.sax.saxutils import escape
from itertools import groupby
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.graphics.shapes import Drawing,Rect,String,Line
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from campaign_hub.reporting.visuals import comparison_panels,value_label

NAVY=colors.HexColor('#11263D')
TEAL=colors.HexColor('#087F80')
MUTED=colors.HexColor('#8BA0AF')


def bar_chart(panel):
    d=Drawing(475,146)
    values=panel['values']; maximum=max(values,default=0)*1.15 or 1
    x=128; width=260; n=len(values); step=min(25,108/max(1,n))
    d.add(Line(x,18,x,137,strokeColor=colors.HexColor('#D4DEE4'),strokeWidth=.6))
    d.add(Line(x,18,x+width,18,strokeColor=colors.HexColor('#D4DEE4'),strokeWidth=.6))
    d.add(String(x,5,'0',fontName='Helvetica',fontSize=8,fillColor=MUTED))
    d.add(String(x+width,5,value_label(maximum,panel['unit']),textAnchor='end',fontName='Helvetica',fontSize=8,fillColor=MUTED))
    for i,(label,value) in enumerate(zip(panel['labels'],values)):
        y=126-i*step
        d.add(String(x-10,y-3,label,textAnchor='end',fontName='Helvetica',fontSize=9,fillColor=NAVY))
        length=value/maximum*width
        d.add(Rect(x,y-6,length,13,fillColor=TEAL if i in panel['highlights'] else MUTED,strokeColor=None))
        d.add(String(x+length+6,y-3,value_label(value,panel['unit']),fontName='Helvetica-Bold',fontSize=9,fillColor=NAVY))
    return d


def render_pdf(packet,citation_text):
    styles=getSampleStyleSheet()
    for name,size,leading,color in [('Title',31,36,NAVY),('Heading',23,28,NAVY),('Panel',15,19,NAVY),
        ('Body',10.5,15,NAVY),('Small',8,11,colors.HexColor('#536778')),('Insight',10,14,NAVY)]:
        styles.add(ParagraphStyle(name='Client'+name,fontName='Helvetica-Bold' if name in ('Title','Heading','Panel') else 'Helvetica',
            fontSize=size,leading=leading,textColor=color,spaceAfter=10))
    def para(text,style='Body'):
        return Paragraph(escape(text).replace('\n','<br/>'),styles['Client'+style])
    def cite(ids):
        return citation_text(packet,{'citations':ids})
    def section_body(section):
        return [para(section['title'],'Heading')]+[para(p) for p in section['text'].split('\n\n')]+[para(cite(section['citations']),'Small')]
    story=[Spacer(1,55),para('CAMPAIGN INTELLIGENCE HUB','Small'),Spacer(1,20),para('Campaign Performance Report','Title'),
        Spacer(1,15),para(packet['client_name'],'Heading'),para(packet['campaign_name']),
        para(f"{packet['period']} | Data as of {packet['facts']['as_of']}"),Spacer(1,35),
        para('Results. Context. Decisions.','Panel'),para('A visual review of goals, channels, historical standing and geographic outcomes.'),
        Spacer(1,35),para('SYNTHETIC DEMONSTRATION DATA','Small'),PageBreak()]
    for section in packet['sections'][:2]:
        story.extend(section_body(section));story.append(Spacer(1,18))
    story.append(PageBreak())
    panels=comparison_panels(packet)
    for family,items in groupby(panels,key=lambda p:p['family']):
        items=list(items)
        for start in range(0,len(items),2):
            story.append(para(family,'Heading'))
            for panel in items[start:start+2]:
                insight=Table([[para('What the data shows','Panel')],[para(panel['insight'],'Insight')]],colWidths=[475])
                insight.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#EDF5F4')),
                    ('BOX',(0,0),(-1,-1),.4,colors.HexColor('#C4DEDB')),('LEFTPADDING',(0,0),(-1,-1),12),
                    ('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,0),8)]))
                story.append(KeepTogether([para(panel['title'],'Panel'),bar_chart(panel),para(panel['note'],'Small'),
                    insight,Spacer(1,6),para(cite(panel['citations']),'Small'),Spacer(1,12)]))
            story.append(PageBreak())
    # Explicitly preserve the missing-history disclosure when no benchmark can be drawn.
    absent=[r['channel'].replace('_',' ').title() for r in packet['facts']['history'] if r['status']!='ok']
    if absent:
        story.extend([para('Historical evidence limitations','Heading'),para('No compatible same-client historical cohort: '+', '.join(absent)+'. No historical rank or benchmark is inferred.'),
            para('Industry benchmark: unavailable. Synthetic peers are not a real industry benchmark.'),PageBreak()])
    for section in packet['sections'][3:6]:
        story.extend(section_body(section));story.append(Spacer(1,10))
    story.append(PageBreak())
    for section in packet['sections'][6:]:
        story.extend(section_body(section));story.append(Spacer(1,15))
    def footer(canvas,doc):
        canvas.setStrokeColor(TEAL);canvas.line(55,805,540,805)
        canvas.setFont('Helvetica',8);canvas.setFillColor(NAVY)
        canvas.drawString(55,30,'Campaign Intelligence Hub | Synthetic demonstration')
        canvas.drawRightString(540,30,str(doc.page))
    stream=BytesIO()
    SimpleDocTemplate(stream,pagesize=A4,rightMargin=55,leftMargin=55,topMargin=60,bottomMargin=55,
        title=f"{packet['client_name']} | Campaign Performance Report").build(story,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()
