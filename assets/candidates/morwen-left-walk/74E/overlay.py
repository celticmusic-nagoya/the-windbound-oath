import json, sys
from PIL import Image, ImageDraw
A=json.load(open(sys.argv[1])); vdir=sys.argv[2]; out=sys.argv[3]
X0,Y0,X1,Y1=20,30,260,345
tiles=[]
for k,v in A.items():
    if k.startswith('_'): continue
    im=Image.open(f'{vdir}/{int(k):04d}.png').convert('RGB').crop((X0,Y0,X1,Y1)); im=im.resize((im.width*2,im.height*2),Image.LANCZOS); d=ImageDraw.Draw(im)
    P=lambda p:((p[0]-X0)*2,(p[1]-Y0)*2)
    def seg(a,b,c):
        if a in v and b in v: d.line([P(v[a]),P(v[b])],fill=c,width=3)
    for a,b in (('H','KA'),('KA','AA'),('AA','HeA'),('AA','ToA'),('HeA','ToA')): seg(a,b,(0,180,0))
    for a,b in (('H','KB'),('KB','AB'),('AB','HeB'),('AB','ToB'),('HeB','ToB')): seg(a,b,(220,0,200))
    for w in ('WN','WF'):
        if w in v:
            x,y=P(v[w]); d.rectangle([x-5,y-5,x+5,y+5],outline=(0,0,255),width=2)
    for kk,p in v.items():
        if not isinstance(p,list): continue
        x,y=P(p); d.ellipse([x-4,y-4,x+4,y+4],outline=(0,0,0),width=2)
    d.text((5,5),'f'+k,fill=(0,0,0))
    tiles.append(im)
W=sum(t.width for t in tiles[:5])
o=Image.new('RGB',(W,tiles[0].height*((len(tiles)+4)//5)),'white')
for i,t in enumerate(tiles): o.paste(t,((i%5)*t.width,(i//5)*t.height))
o.save(out)
