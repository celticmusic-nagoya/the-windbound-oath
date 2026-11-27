"""Rebuild exact provisional skirt UV fit trial from verified source archives."""
import hashlib, io, json, pathlib, sys, zipfile
import numpy as np
from PIL import Image

def sha(b): return hashlib.sha256(b).hexdigest()
def archive(p,h):
    raw=pathlib.Path(p).read_bytes(); assert sha(raw)==h
    z=zipfile.ZipFile(io.BytesIO(raw)); assert z.testzip() is None; return z
with archive(sys.argv[1],'a290131b16f8c61ee32d30125e438782ab59e36ffa2ce9c132685cefa71016bc') as z:
    raw=z.read('assets/companions/morwen/reference/morwen-design-sheet-v3.png'); assert sha(raw)=='384268738ff34d653dd5fb9077728d33dbedc7485aae45e5eb6b87d828a472e9'
    s=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB')); assert s.shape==(1536,1024,3)
palette=np.array([np.median(s[1378:1398,x-10:x+10],axis=(0,1)).round().astype(int) for x in [387,430,472,515,557]])
assert palette.tolist()==[[52,38,60],[93,57,116],[160,111,182],[250,240,237],[205,158,108]]
with archive(sys.argv[2],'09150c4f57a3648d813fd63850c14342d0b0e688ea282cbedc27016c03e320e1') as z:
    receipt=json.loads(z.read('receipt.json')); images={}
    for name in ['dark_pleat','plaid_accent']:
        raw=z.read(name+'.png'); assert sha(raw)==receipt['outputs'][name]['sha256']; im=Image.open(io.BytesIO(raw)).convert('RGBA'); assert sha(im.tobytes())==receipt['outputs'][name]['pixel_sha256']; images[name]=np.asarray(im).copy(); assert np.array_equal(images[name][:,:512],images[name][:,512:])
a=images['dark_pleat']; y=a[:,:,:3]@np.array([.2126,.7152,.0722]); delta=y-np.median(y)
dark=a.copy();dark[:,:,:3]=np.clip(np.rint(palette[0]+delta[:,:,None]),0,255).astype(np.uint8)
yy,xx=np.mgrid[:128,:1024]; mod=3.0*np.sin(2*np.pi*(xx%8+yy*.5)/8)+np.clip(np.tile(delta[:128,:512],(1,2)),-10,10)*.7
trim=np.zeros((128,1024,4),dtype=np.uint8); stripe=np.maximum(np.clip(5.5-np.abs(yy-84),0,1),np.clip(2.0-np.abs(yy-99),0,1));trim[:,:,:3]=np.clip(np.rint(palette[4]+mod[:,:,None]),0,255).astype(np.uint8);trim[:,:,3]=np.rint(255*stripe).astype(np.uint8);trim[trim[:,:,3]==0,:3]=0
N=512; yy,xx=np.mgrid[:N,:N]; layers=((1,0,.50,.40,.52),(1,1,.50,.37,.30),(2,0,.235,.075,.66),(2,1,.24,.085,.63),(2,0,.735,.045,.48),(2,1,.74,.055,.45),(3,0,.49,.018,.82),(3,1,.46,.016,.77),(3,1,.55,.016,.77))
colors=palette[[1,2,0,4]];rgb=np.broadcast_to(colors[0],(N,N,3)).astype(float).copy()
for i,axis,c,w,a0 in layers:
    coord=yy if axis else xx
    q=np.clip((w/2+1/N-np.abs((coord/N-c+.5)%1-.5))*N,0,1)*a0
    rgb=rgb*(1-q[:,:,None])+colors[i]*q[:,:,None]
carrier=a[:,:N,:3]@np.array([.2126,.7152,.0722]);factor=carrier/np.median(carrier)
rgb=np.clip(np.rint(rgb*factor[:,:,None]),0,255).astype(np.uint8); tile=np.concatenate([rgb,np.full((N,N,1),255,dtype=np.uint8)],axis=2);plaid=np.tile(tile,(1,2,1))
expected=['42004bf87da39e527e04e60b9295da9a0af73d1983596633c6493ab777008ac0','50402be36cc843e11d8b34ecf9998ca522d852fc9fdb6c55b3802939739bcd81','7fd250ab5d677ac73996129e12da7c142bef09e259e644082630a3be4256909a']
assert [sha(x.tobytes()) for x in (dark,plaid,trim)]==expected
# Full plaid repeat; coarse diagnostic placement, not a production UV mask.
tile=np.array(Image.fromarray(plaid[:,:512]).resize((96,96),Image.Resampling.LANCZOS));result=dark.copy();result[:,464:560]=tile[np.arange(512)%96]
y=np.arange(448,512); t=trim[(y-12)%128]; alpha=t[:,:,3,None].astype(np.int32);old=result[448:,:,:3].astype(np.int32);result[448:,:,:3]=((t[:,:,:3].astype(np.int32)*alpha+old*(255-alpha)+127)//255).astype(np.uint8)
assert np.array_equal(result[:,:,3],dark[:,:,3]);assert np.array_equal(result[:448,:464],dark[:448,:464]);assert np.array_equal(result[:448,560:],dark[:448,560:]);assert sha(result.tobytes())=='cc42bb0faf2881a1e258389b99b48a959495fdb2bd062611326ed24bed4a13fd'
out=pathlib.Path(sys.argv[3]);assert not out.exists();Image.fromarray(result).save(out);assert np.array_equal(np.asarray(Image.open(out)),result)
print(json.dumps({'scope':'VOLATILE_UV_FIT_TRIAL_ONLY','source_pixels':expected,'pixel_sha256':sha(result.tobytes()),'png_sha256':sha(out.read_bytes()),'alpha_exact':True,'reopen_exact':True}))
