import sys
from PIL import Image, ImageDraw
d=sys.argv[1]; names=["front","right","back","left","face_front","face_q3"]
ims=[Image.open(f"{d}/A_baseline_{n}.png").convert("RGBA") for n in names]
H=800; tiles=[]
for im in ims:
    bg=Image.new("RGBA",im.size,(58,58,66,255)); bg.alpha_composite(im); tiles.append(bg.resize((int(im.width*H/im.height),H)))
W=sum(t.width for t in tiles); sheet=Image.new("RGB",(W,H+30),(20,20,24)); x=0; dr=ImageDraw.Draw(sheet)
for n,t in zip(names,tiles): sheet.paste(t.convert("RGB"),(x,30)); dr.text((x+8,8),"A baseline: "+n,fill=(230,230,230)); x+=t.width
sheet.save(f"{d}/A_BASELINE_SHEET.png"); print(sheet.size)
