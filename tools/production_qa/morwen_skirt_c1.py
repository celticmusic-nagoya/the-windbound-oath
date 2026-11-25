"""C1 skirt atlas trial; physical geometry and projected landmarks unverified."""
import hashlib, io, json, pathlib, sys, zipfile
import numpy as np
from PIL import Image

def sha(b): return hashlib.sha256(b).hexdigest()
def build(source, out):
    raw=pathlib.Path(source).read_bytes()
    assert sha(raw)=='09150c4f57a3648d813fd63850c14342d0b0e688ea282cbedc27016c03e320e1'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        b=z.read('dark_pleat.png')
        assert sha(b)=='b462d60bbfbeb355587b87b5cd0e40bcae289bfd2d66f26c1b7e213b447c2f62'
    a=np.array(Image.open(io.BytesIO(b)))
    assert a.shape==(512,1024,4) and sha(a.tobytes())=='9c1bd62532498b62163e41ef9b820eb15cb0df41eba7ace94a2dacd22706a9a7'
    w=np.array([.2126,.7152,.0722]); l=a[:,:,:3]@w; d=l-np.median(l)
    dark=a.copy(); dark[:,:,:3]=np.clip(np.rint(np.array([52,38,60])+d[:,:,None]),0,255).astype(np.uint8)
    assert sha(dark.tobytes())=='42004bf87da39e527e04e60b9295da9a0af73d1983596633c6493ab777008ac0'
    y,x=np.mgrid[:512,:1024]; u=(x-512)%96; v=y%96
    rgb=np.broadcast_to(np.array([99,53,126.]),(512,1024,3)).copy()
    for t in (u,v):
        q=(np.abs(t-48)<=21)*.65; rgb=rgb*(1-q[...,None])+np.array([163,96,184])*q[...,None]
        q=((np.abs(t-22)<=4)|(np.abs(t-74)<=4))*.65; rgb=rgb*(1-q[...,None])+np.array([55,32,70])*q[...,None]
    gold=((u>=43)&(u<46))|((u>=50)&(u<53))|((v>=43)&(v<46))|((v>=50)&(v<53))
    delta=np.clip(dark[:,:,:3].astype(float)@w-np.median(dark[:,:,:3]@w),-5,5)
    rgb[gold]=[205,158,108]; rgb=np.clip(np.rint(rgb+delta[...,None]),0,255).astype(np.uint8)
    trim=np.clip(np.rint(np.array([205,158,108])+delta[...,None]),0,255).astype(np.uint8)
    oldpanel=(x>=416)&(x<608); oldbands=((y>=458)&(y<464))|((y>=474)&(y<480))
    old=dark.copy(); old[oldpanel,:3]=rgb[oldpanel]; old[oldbands,:3]=trim[oldbands]
    assert sha(old.tobytes())=='eae608424f24c14c946b7d94f70282076a66a436dd989ed92589ad12c04e8efd'
    # Narrow right-front placement; maintain pattern phase and measured microvariation.
    panel=(x>=395)&(x<495); bands=((y>=482)&(y<488))|((y>=498)&(y<504))
    c=dark.copy(); c[:,:,:3]=np.clip(np.rint(np.array([34,25,40])+d[...,None]),0,255).astype(np.uint8)
    c[panel,:3]=rgb[panel]; c[bands,:3]=trim[bands]
    assert np.array_equal(c[:,:,3],old[:,:,3]) and np.all(c[:,:,3]==255)
    assert np.array_equal(c[panel&~bands,:3],rgb[panel&~bands])
    assert np.all(bands.sum(axis=0)==12) and np.all(panel.sum(axis=1)==100)
    assert np.array_equal(c[bands,:3],trim[bands])
    base=c[~(panel|bands),:3]; assert np.max(base)<=46
    out=pathlib.Path(out); out.mkdir(exist_ok=False)
    for name,im in [('A-reconstructed',old),('C1',c)]:
        p=out/(name+'.png'); Image.fromarray(im).save(p); assert np.array_equal(np.array(Image.open(p)),im)
    report={'scope':'VOLATILE_ATLAS_TRIAL_NOT_ADOPTED','source_archive_sha256':sha(raw),'A_rgba_sha256':sha(old.tobytes()),'C1_rgba_sha256':sha(c.tobytes()),'C1_png_sha256':sha((out/'C1.png').read_bytes()),'panel_x_half_open':[395,495],'trim_y_half_open':[[482,488],[498,504]],'dark_median_rgb':np.median(base,axis=0).tolist(),'alpha_exact':True,'plaid_palette_phase_exact':True,'native_projection':'NOT_RUN','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'}
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
if __name__=='__main__': build(sys.argv[1],sys.argv[2])
