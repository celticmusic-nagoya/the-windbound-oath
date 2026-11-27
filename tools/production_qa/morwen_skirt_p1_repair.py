"""P1 repair candidates. Atlas-space only; no claim of canonical UV or geometry."""
import hashlib,json,sys,pathlib
import numpy as np
from PIL import Image,ImageDraw

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,h):
    p=pathlib.Path(p);assert sha(p.read_bytes())==h
    with Image.open(p) as im:
        assert im.mode=='RGBA' and im.size==(1024,512)
        return np.array(im)
def sat(a):
    a=a.astype(float);hi=a.max(-1);lo=a.min(-1);return float(np.median((hi-lo)/np.maximum(hi,1)))
def build(dark,old,out):
    out=pathlib.Path(out);out.mkdir(exist_ok=False)
    assert np.all(dark[:,:,3]==255) and np.array_equal(dark[:,:,3],old[:,:,3])
    N=96;y,x=np.mgrid[:512,:1024];u=(x-512)%N;v=y%N
    # Equal paired gold rules in each direction. Repeat and UV size are trial choices.
    rgb=np.broadcast_to(np.array([99,53,126.]),(512,1024,3)).copy()
    for a in (u,v):
        q=(np.abs(a-48)<=21)*.65
        rgb=rgb*(1-q[...,None])+np.array([163,96,184])*q[...,None]
        q=((np.abs(a-22)<=4)|(np.abs(a-74)<=4))*.65
        rgb=rgb*(1-q[...,None])+np.array([55,32,70])*q[...,None]
    gold=((u>=43)&(u<46))|((u>=50)&(u<53))|((v>=43)&(v<46))|((v>=50)&(v<53))
    # Preserve scan-derived low-amplitude variation, no directional lighting.
    delta=np.clip(dark[:,:,:3].astype(float)@np.array([.2126,.7152,.0722])-np.median(dark[:,:,:3]@np.array([.2126,.7152,.0722])),-5,5)
    rgb[gold]=[205,158,108];rgb=np.clip(np.rint(rgb+delta[...,None]),0,255).astype(np.uint8)
    bands=((y>=458)&(y<464))|((y>=474)&(y<480))
    report={'scope':'P1_VOLATILE_ATLAS_CANDIDATES_NOT_D4','prior_pixel_sha256':sha(old.tobytes()),'dark_pixel_sha256':sha(dark.tobytes()),'old_panel_width_px':96,'repeat_px':96,'gold_rule_width_px':3,'gold_rule_centers_each_axis':[44,51],'trim_rows_half_open':[[458,464],[474,480]],'old_plaid_atlas_median_s':sat(old[320:448,464:560,:3]),'note':'Widths 192/256 and trim lift are hypotheses, not screen-space targets. Rear mapping remains unresolved. No native save.','outputs':[]}
    sheet=Image.new('RGB',(1048,3*280),(25,25,31));draw=ImageDraw.Draw(sheet)
    for i,(name,w) in enumerate((('A',192),('B',256)),1):
        panel=(x>=512-w//2)&(x<512+w//2);a=dark.copy();a[panel,:3]=rgb[panel];a[bands,:3]=np.clip(np.rint(np.array([205,158,108])+delta[bands,None]),0,255).astype(np.uint8)
        assert np.array_equal(a[:,:,3],old[:,:,3]);assert np.array_equal(a[~(panel|bands)],dark[~(panel|bands)])
        assert np.all(bands.sum(axis=0)==12);assert np.array_equal(gold[:96,:96],gold[96:192,:96]);assert np.array_equal(gold[:96,:96],gold[:96,96:192])
        p=out/f'candidate-{name}.png';Image.fromarray(a).save(p);assert np.array_equal(np.asarray(Image.open(p)),a)
        report['outputs'].append({'name':p.name,'panel_width_px':w,'panel_x_half_open':[512-w//2,512+w//2],'plaid_median_s':sat(a[320:448,512-w//2:512+w//2,:3]),'png_sha256':sha(p.read_bytes()),'pixel_sha256':sha(a.tobytes())})
        draw.text((12,i*280+6),f'{name} | {w}px panel | paired gold | raised equal trim',fill='white');sheet.paste(Image.fromarray(a).convert('RGB').resize((1024,256)),(12,i*280+24))
    draw.text((12,6),'Previous | 96px panel | native G2 FAIL',fill='white');sheet.paste(Image.fromarray(old).convert('RGB').resize((1024,256)),(12,24));sheet.save(out/'comparison.png')
    report['comparison_sha256']=sha((out/'comparison.png').read_bytes());(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    build(load(sys.argv[1],'7b5558f4d6a548cd15e7803161532c8fbad5e98b25ffc49e094ae646a882ae83'),load(sys.argv[2],'20f7d59ca5668c9816a8681c44973ffd56a04b50e8fab7a28b09e5e350dae5f6'),sys.argv[3])
