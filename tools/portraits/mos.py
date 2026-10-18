from PIL import Image,ImageDraw
def mosaic(items,box,z,out,step=10,cols=3):
    w=(box[2]-box[0])*z;h=(box[3]-box[1])*z;rows=(len(items)+cols-1)//cols;S=Image.new('RGB',(w*cols,h*rows))
    for i,(k,im) in enumerate(items):
        bg=Image.new('RGBA',im.size,(128,128,128,255));bg.alpha_composite(im.convert('RGBA'))
        c=bg.convert('RGB').crop(box).resize((w,h),Image.LANCZOS);d=ImageDraw.Draw(c);d.text((3,3),k,fill=(255,255,0))
        for x in range((box[0]//step+1)*step,box[2],step):
            d.line([((x-box[0])*z,0),((x-box[0])*z,8 if x%20 else 14)],fill=(255,255,255))
            if x%20==0:d.text(((x-box[0])*z+2,14),str(x),fill=(255,255,255))
        for y in range((box[1]//step+1)*step,box[3],step):
            d.line([(0,(y-box[1])*z),(8 if y%20 else 14,(y-box[1])*z)],fill=(255,255,255))
            if y%20==0:d.text((16,(y-box[1])*z-5),str(y),fill=(255,255,255))
        S.paste(c,((i%cols)*w,(i//cols)*h))
    S.save(out)
IDS=['01','02','03','04','05','06','07','08'];NM=['normal','smile','angry','sad','surprised','worried','determined','relieved']
SRC={i:(1 if k<4 else 0,k%4) for k,i in enumerate(IDS)}   # id -> (sheet idx, panel)
def items(ch):
    L=[('master',Image.open(f'{ch}_master.png'))]
    for i,n in zip(IDS,NM):
        s,p=SRC[i];L.append((f'{i} {n}',Image.open(f'warp/{ch}_{s}{p}.png')))
    return L
if __name__=='__main__':
    mosaic(items('fiona'),(495,235,705,400),3,'m_fiona.png')
    mosaic(items('lou'),(670,370,890,520),3,'m_lou.png')
