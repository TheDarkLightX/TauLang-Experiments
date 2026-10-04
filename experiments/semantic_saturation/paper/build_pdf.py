"""Typeset the editable manuscript with Pandoc parsing and ReportLab layout.

Only paper-local deliverables and ignored build intermediates are written.
The fonts and PNG figures are local; no network retrieval or publication occurs.
"""
from pathlib import Path
import html
import json
import re
import subprocess
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from PIL import Image as PILImage

HERE=Path(__file__).resolve().parent
BUILD=HERE/'.build';BUILD.mkdir(exist_ok=True)
FONT=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Serif','DejaVuSerif.ttf'),('SerifBold','DejaVuSerif-Bold.ttf'),('SerifItalic','DejaVuSerif-Italic.ttf'),('SerifBoldItalic','DejaVuSerif-BoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='SerifBold',italic='SerifItalic',boldItalic='SerifBoldItalic')
base=ParagraphStyle('body',fontName='Serif',fontSize=10,leading=14.1,spaceAfter=7,alignment=TA_LEFT,
    allowWidows=0,allowOrphans=0,splitLongWords=1,textColor=colors.HexColor('#181818'))
styles={'body':base,
 'title':ParagraphStyle('title',parent=base,fontName='SerifBold',fontSize=20,leading=25,spaceAfter=12,keepWithNext=True),
 'section':ParagraphStyle('section',parent=base,fontName='SerifBold',fontSize=13,leading=17,spaceBefore=14,spaceAfter=7,keepWithNext=True),
 'subsection':ParagraphStyle('subsection',parent=base,fontName='SerifBold',fontSize=11,leading=15,spaceBefore=9,spaceAfter=5,keepWithNext=True),
 'caption':ParagraphStyle('caption',parent=base,fontSize=8.7,leading=12,spaceAfter=12),
 'table':ParagraphStyle('table',parent=base,fontSize=8.4,leading=11.2,spaceAfter=0),
 'tablehead':ParagraphStyle('tablehead',parent=base,fontName='SerifBold',fontSize=8.4,leading=11.2,spaceAfter=0),
 'list':ParagraphStyle('list',parent=base,leftIndent=12,firstLineIndent=-9,spaceAfter=4),
 'date':ParagraphStyle('date',parent=base,fontSize=9,leading=12,spaceAfter=9)}

def inline(items):
    out=[]
    for item in items:
        t=item['t'];c=item.get('c')
        if t=='Str':out.append(html.escape(c))
        elif t in ('Space','SoftBreak'):out.append(' ')
        elif t=='LineBreak':out.append('<br/>')
        elif t=='Strong':out.append('<b>'+inline(c)+'</b>')
        elif t=='Emph':out.append('<i>'+inline(c)+'</i>')
        elif t=='Code':out.append('<font name="Courier" size="8.5">'+html.escape(c[1])+'</font>')
        elif t=='Link':out.append('<link href="'+html.escape(c[2][0],quote=True)+'" color="#214F74">'+inline(c[1])+'</link>')
        elif t=='Quoted':out.append('&quot;'+inline(c[1])+'&quot;')
        elif t=='Math':out.append(html.escape(c[1]))
        elif t=='Span':out.append(inline(c[1]))
        else:raise ValueError('unsupported inline '+t)
    return ''.join(out)

def block_text(blocks):
    return '<br/>'.join(inline(b['c']) for b in blocks if b['t'] in ('Plain','Para'))

def make_table(c):
    head=c[3][1];body=[]
    for tablebody in c[4]:body.extend(tablebody[3])
    raw=head+body
    cells=[[block_text(cell[4]) for cell in row[1]] for row in raw]
    headers=[re.sub('<[^>]+>','',x) for x in cells[0]]
    n=len(headers)
    if n==3:widths=[114,226,164]
    elif n==7 and headers[0]=='Family':widths=[120,42,58,67,77,53,87]
    elif n==7:widths=[133,51,50,70,58,62,80]
    elif n==4 and 'First arm' in headers[0]:widths=[279,60,60,105]
    elif n==4:widths=[228,108,84,84]
    else:widths=[504/n]*n
    rows=[[Paragraph(text,styles['tablehead' if i==0 else 'table']) for text in row] for i,row in enumerate(cells)]
    table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EDF1')),
      ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#CCD2D7')),
      ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),5),
      ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return [Spacer(1,4),table,Spacer(1,10)]

def image_para(block):
    return block['t']=='Para' and len(block['c'])==1 and block['c'][0]['t']=='Image'

ast=json.loads(subprocess.check_output(['pandoc','--from','markdown-implicit_figures-superscript-subscript','--to','json',str(HERE/'MANUSCRIPT.md')],text=True))
(BUILD/'manuscript-ast.json').write_text(json.dumps(ast,ensure_ascii=False))
flow=[];blocks=ast['blocks'];i=0
while i<len(blocks):
    block=blocks[i];t=block['t'];c=block.get('c')
    if image_para(block):
        im=c[0]['c'];path=HERE/Path(im[2][0]).with_suffix('.png')
        with PILImage.open(path) as pixels:w,h=pixels.size
        width=504;height=width*h/w
        if height>612:height=612;width=height*w/h
        figure=Image(str(path),width=width,height=height);figure.hAlign='CENTER'
        group=[Spacer(1,7),figure,Spacer(1,7)]
        if i+1<len(blocks) and blocks[i+1]['t']=='Para' and inline(blocks[i+1]['c']).startswith('Figure '):
            i+=1;group.append(Paragraph(inline(blocks[i]['c']),styles['caption']))
        flow.append(KeepTogether(group))
    elif t=='Header':
        level=c[0];style='title' if level==1 else 'section' if level==2 else 'subsection'
        flow.append(Paragraph(inline(c[2]),styles[style]))
    elif t in ('Para','Plain'):
        text=inline(c);style='date' if text.startswith('Research manuscript draft') else 'body'
        flow.append(Paragraph(text,styles[style]))
    elif t=='Table':flow.extend(make_table(c))
    elif t in ('BulletList','OrderedList'):
        items=c if t=='BulletList' else c[1]
        start=1 if t=='BulletList' else c[0][0]
        for j,item in enumerate(items):
            prefix='• ' if t=='BulletList' else str(start+j)+'. '
            flow.append(Paragraph(prefix+block_text(item),styles['list']))
        flow.append(Spacer(1,4))
    else:raise ValueError('unsupported block '+t)
    i+=1

output=HERE/'checked-semantic-saturation.pdf'
doc=SimpleDocTemplate(str(output),pagesize=letter,rightMargin=54,leftMargin=54,topMargin=49,bottomMargin=48,
 title='Checked semantic saturation for a restricted atomless Boolean algebra fragment',author='',
 subject='Finite-support reference semantics and attribution-controlled Tau optimization experiments',pageCompression=1)
def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Serif',8);canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(54,26,'Checked semantic saturation')
    canvas.drawRightString(558,26,str(doc.page));canvas.restoreState()
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(output)
