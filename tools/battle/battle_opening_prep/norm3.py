import numpy as np,pickle,sys,os
from PIL import Image
# usage: norm3.py <set> <refIdx> <target bbox display px> <target centroid screen x> [bm_display]
S,REF,TARGET,CX=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]);BM_D=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
BOXW,BOXH=158.0,198.0;M=8
cl=pickle.load(open(S+'_clean.pkl','rb'));info=[]
def cen(f):
    a=f[...,3].astype(float);ys,xs=np.mgrid[0:a.shape[0],0:a.shape[1]];return (a*xs).sum()/a.sum()
for f in cl:
    al=f[...,3];ys,xs=np.where(al>=128);bot=ys.max();band=ys>bot-45;ax=xs[band].mean()
    ys2,xs2=np.where(al>16);info.append((bot,ax,ys2.min(),xs2.min(),xs2.max(),cen(f)))
body=info[REF][0]-info[REF][2]
W=int(round(body*BOXW/TARGET/2)*2);BM=int(np.ceil(BM_D*W/BOXW))
L=max(ax-x0 for b,ax,t,x0,x1,c in info);R=max(x1-ax for b,ax,t,x0,x1,c in info);T=max(b-t for b,ax,t,x0,x1,c in info)
H=int(np.ceil(T+M+BM));H+=H%2
axpos=CX*W/BOXW-(info[REF][5]-info[REF][1]);AX=axpos/W
assert axpos-L>=M and W-axpos-R>=M,('canvas too narrow',W,axpos,L,R)
sc=min(BOXW/W,BOXH/H);print(S,'canvas',W,H,'AX',round(AX,3),'BM',BM,'scale',round(sc,4),'display bbox ref',round(body*sc,1),'L/R',round(L),round(R),'T',T)
os.makedirs('out_'+S,exist_ok=True)
for i,(f,(bot,ax,top,x0,x1,c)) in enumerate(zip(cl,info),1):
    canvas=Image.new('RGBA',(W,H),(0,0,0,0));px=int(round(axpos-ax));py=int(round(H-BM-1-bot))
    canvas.alpha_composite(Image.fromarray(f),(px,py))
    a=np.array(canvas)[...,3];yy,xx=np.where(a>16);assert xx.min()>=2 and xx.max()<W-2 and yy.min()>=2,'clipped'
    print(' frame',i,'bbox',xx.min(),yy.min(),xx.max()+1,yy.max()+1,'feetbottom',yy.max()+1)
    o=np.array(canvas);o[o[...,3]==0]=0;Image.fromarray(o).save('out_%s/%s_%02d.png'%(S,S,i),optimize=True)
