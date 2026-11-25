"""Reproducible 2D plaid material candidate; no UV or native geometry edits."""
import hashlib, io, json, pathlib, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw

def sha(b): return hashlib.sha256(b).hexdigest()
def run(sheet_zip, textile_zip, out):
    out=pathlib.Path(out); out.mkdir(exist_ok=False)
    def archive(p,h):
        raw=pathlib.Path(p).read_bytes(); assert sha(raw)==h
        z=zipfile.ZipFile(io.BytesIO(raw)); assert z.testzip() is None; return z
    with archive(sheet_zip,'a290131b16f8c61ee32d30125e438782ab59e36ffa2ce9c132685cefa71016bc') as z:
        raw=z.read('assets/companions/morwen/reference/morwen-design-sheet-v3.png'); assert sha(raw)=='384268738ff34d653dd5fb9077728d33dbedc7485aae45e5eb6b87d828a472e9'
        s=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB')); assert s.shape==(1536,1024,3)
    palette=np.array([np.median(s[1378:1398,x-10:x+10],axis=(0,1)).round().astype(int) for x in [387,430,472,515,557]])
    assert palette.tolist()==[[52,38,60],[93,57,116],[160,111,182],[250,240,237],[205,158,108]]
    with archive(textile_zip,'09150c4f57a3648d813fd63850c14342d0b0e688ea282cbedc27016c03e320e1') as z:
        receipt=json.loads(z.read('receipt.json')); images={}
        for name in ['dark_pleat','plaid_accent']:
            raw=z.read(name+'.png'); assert sha(raw)==receipt['outputs'][name]['sha256']; im=Image.open(io.BytesIO(raw)).convert('RGBA'); assert sha(im.tobytes())==receipt['outputs'][name]['pixel_sha256']; images[name]=np.asarray(im).copy(); assert np.array_equal(images[name][:,:512],images[name][:,512:])
    N=512; yy,xx=np.mgrid[:N,:N]; layers=((1,0,.50,.40,.52),(1,1,.50,.37,.30),(2,0,.235,.075,.66),(2,1,.24,.085,.63),(2,0,.735,.045,.48),(2,1,.74,.055,.45),(3,0,.49,.018,.82),(3,1,.46,.016,.77),(3,1,.55,.016,.77))
    # Retain exact earlier authored pattern spacing; palette anchors only change.
    # Purple ground, lighter woven crossing, darkest stripe, gold narrow highlight.
    colors=palette[[1,2,0,4]]
    rgb=np.broadcast_to(colors[0],(N,N,3)).astype(float).copy()
    for i,axis,c,w,a in layers:
        coord=yy if axis else xx
        q=np.clip((w/2+1/N-np.abs((coord/N-c+.5)%1-.5))*N,0,1)*a
        rgb=rgb*(1-q[:,:,None])+colors[i]*q[:,:,None]
    # The dark swatch is a quantized carrier for the measured source detail, not raw scan.
    carrier=images['dark_pleat'][:,:N,:3]@np.array([.2126,.7152,.0722]); factor=carrier/np.median(carrier)
    rgb=np.clip(np.rint(rgb*factor[:,:,None]),0,255).astype(np.uint8)
    tile=np.concatenate([rgb,np.full((N,N,1),255,dtype=np.uint8)],axis=2); arr=np.tile(tile,(1,2,1)); assert np.array_equal(arr[:,:N],arr[:,N:]); assert np.array_equal(arr[:,:,3],images['plaid_accent'][:,:,3]); assert np.all(arr[:,:,:3].min(axis=(0,1))>=0)
    target=out/'plaid_palette_calibrated.png'; Image.fromarray(arr).save(target); assert Image.open(target).convert('RGBA').tobytes()==arr.tobytes()
    before=images['plaid_accent']; diff=np.abs(arr[:,:,:3].astype(float)-before[:,:,:3]); seam=np.abs(arr[:,511,:3].astype(float)-arr[:,512,:3]).mean(); p95=np.percentile(np.abs(np.diff(arr[:,:,:3].astype(float),axis=1)).mean(axis=2),95)
    preview=Image.new('RGB',(1024,580),(26,25,32)); d=ImageDraw.Draw(preview);d.text((12,10),'Previous authored plaid + measured detail',fill='white'); d.text((524,10),'Official-palette plaid + measured detail',fill='white'); preview.paste(Image.fromarray(before[:,:512]).convert('RGB'),(0,32)); preview.paste(Image.fromarray(tile).convert('RGB'),(512,32)); d.text((12,555),'2D material candidate only | same stripe spacing | UV fit and scale not evaluated',fill='white'); preview.save(out/'comparison.png')
    result={'scope':'2D_SWATCH_ONLY_NOT_ADOPTED','palette':palette.tolist(),'anchors':colors.tolist(),'source_textile_archive_sha256':'09150c4f57a3648d813fd63850c14342d0b0e688ea282cbedc27016c03e320e1','mean_abs_rgb_change':float(diff.mean()),'mean_repeat_seam_abs_rgb':float(seam),'interior_adjacent_mean_rgb_p95':float(p95),'alpha_exact':True,'repeat_exact':True,'output_sha256':sha(target.read_bytes()),'pixel_sha256':sha(arr.tobytes()),'comparison_sha256':sha((out/'comparison.png').read_bytes()),'limitations':['Not a new measured source; detail reconstructed from quantized dark swatch','Pattern spacing inherited, not canonical measurement','No UV, physical scale or native fit verification']}; (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': run(*sys.argv[1:])
