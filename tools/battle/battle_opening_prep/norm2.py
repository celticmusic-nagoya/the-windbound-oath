import numpy as np,pickle,sys,os
from PIL import Image
w,TARGET,AX=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]);BOXW,BOXH=158.0,198.0;M=8;BM=3
cl=pickle.load(open('%s_clean.pkl'%w,'rb'));info=[]
for f in cl:
    al=f[...,3];ys,xs=np.where(al>=128);bot=ys.max();band=ys>bot-45;ax=xs[band].mean()
    ys2,xs2=np.where(al>16);info.append((bot,ax,ys2.min(),xs2.min(),xs2.max()))
body6=info[5][0]-info[5][2]
L=max(ax-x0 for b,ax,t,x0,x1 in info);R=max(x1-ax for b,ax,t,x0,x1 in info);T=max(b-t for b,ax,t,x0,x1 in info)
W=int(round(body6*BOXW/TARGET/2)*2);H=int(np.ceil(T+M+BM));H+=H%2
need=max((L+M)/AX,(R+M)/(1-AX));assert W>=need,('canvas too narrow',W,need)
sc=min(BOXW/W,BOXH/H);print(w,'canvas',W,H,'box scale',round(sc,4),'body6',body6,'-> display body',round(body6*sc,1),'L,R,T',round(L),round(R),T,'feet-bottoms',[b for b,*_ in info])
os.makedirs('out_%s'%w,exist_ok=True);name='aidan_draw' if w=='aidan' else 'fiona_ready'
for i,(f,(bot,ax,top,x0,x1)) in enumerate(zip(cl,info),1):
    canvas=Image.new('RGBA',(W,H),(0,0,0,0));im=Image.fromarray(f)
    px=int(round(W*AX-ax));py=int(round(H-BM-bot-1));canvas.alpha_composite(im.crop((0,0,im.width,im.height)),(px,py)) if px>=0 and py>=0 else None
    if px<0 or py<0: canvas.alpha_composite(im.crop((max(0,-px),max(0,-py),im.width,im.height)),(max(px,0),max(py,0)))
    a=np.array(canvas)[...,3];yy,xx=np.where(a>16);print(' frame',i,'bbox',xx.min(),yy.min(),xx.max()+1,yy.max()+1)
    canvas.save('out_%s/%s_%02d.png'%(w,name,i),optimize=True)
