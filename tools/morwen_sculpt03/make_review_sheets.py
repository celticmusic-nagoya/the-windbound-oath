"""Contact sheets for QA, with explicit partial-prototype labels. No art retouching."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path('qa_output/morwen-sculpt03')
DEST = Path('docs/qa/morwen-sculpt03')
DEST.mkdir(parents=True, exist_ok=True)
VIEWS = ['front','character_left','character_right','back','three_quarter','three_quarter_other']

def paste(sheet, path, xy, size):
    with Image.open(path) as src:
        src = src.convert('RGBA').resize((size,size), Image.Resampling.LANCZOS)
        sheet.paste(src,xy,src)

for mode in ['color','clay']:
    sheet = Image.new('RGB',(768,586),(35,38,44)); draw = ImageDraw.Draw(sheet)
    draw.text((12,8),'SCULPT03 LOCAL EYELID STUDY - NOT INTEGRATED / NOT FINAL ART',fill='white')
    draw.text((12,24),'Inherited SCULPT02 face + hair retained. G1 BLOCKED; full G2 FAIL.',fill='white')
    for i,view in enumerate(VIEWS):
        x=(i%3)*256; y=46+(i//3)*270
        paste(sheet,ROOT/'review'/f'{mode}_{view}.png',(x,y),256)
        draw.text((x+5,y+254),view,fill='white')
    sheet.save(DEST/f'{mode}_context_sheet.png')

for size in [64,128]:
    sheet = Image.new('RGB',(size*6,68+size*2+36),(35,38,44));draw=ImageDraw.Draw(sheet)
    draw.text((5,5),f'{size}px QA: TOP SCULPT02 / BOTTOM LOCAL STUDY',fill='white')
    draw.text((5,22),'UNAPPROVED; not a completed face/hair replacement',fill='white')
    for row,folder in enumerate(['baseline','review']):
        for col,view in enumerate(VIEWS):
            paste(sheet,ROOT/folder/f'color_{view}.png',(col*size,50+row*(size+22)),size)
            draw.text((col*size+2,50+row*(size+22)+size),view[:10],fill='white')
    sheet.save(DEST/f'comparison_{size}px.png')

names=['isolated_blink_open','isolated_blink_half','isolated_blink_closed',
       'isolated_control_wire_front','isolated_control_wire_three_quarter']
sheet=Image.new('RGB',(768,586),(35,38,44));draw=ImageDraw.Draw(sheet)
draw.text((10,7),'LOCAL OPEN EYELID PATCHES - blink diagnostic, NOT a completed rig',fill='white')
draw.text((10,25),'Control cage wireframes / source face hidden for isolation only',fill='white')
for i,name in enumerate(names):
    x=i%3*256; y=46+i//3*270
    paste(sheet,ROOT/'review'/(name+'.png'),(x,y),256)
    draw.text((x+3,y+254),name.replace('isolated_',''),fill='white')
sheet.save(DEST/'local_topology_and_blink_sheet.png')
