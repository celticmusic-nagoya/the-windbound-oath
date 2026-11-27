"""Exploratory CC0 textile finishing; no model edits or inferred UV assignment."""
import hashlib, io, json, math, pathlib, sys, zipfile
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

SOURCE='https://ambientcg.com/a/Fabric085'
LICENSE='https://docs.ambientcg.com/license/'
BASE_PIXEL_SHA='cdebf9c8f521085d9dc389f41c719d2b2d2a9e1c64ec49f3f4b58af66e2d36ff'
def sha(b): return hashlib.sha256(b).hexdigest()
def load_map(z, suffix):
    hits=[i for i in z.infolist() if i.filename.rsplit('/',1)[-1].lower().endswith(suffix.lower()) and i.filename.rsplit('/',1)[-1].lower().startswith('fabric085_')]
    if len(hits)!=1: raise ValueError(f'nonunique or absent {suffix}: {len(hits)}')
    item=hits[0]
    if not 0<item.file_size<=20_000_000: raise ValueError('map size')
    b=z.read(item); im=Image.open(io.BytesIO(b)); im.load()
    if im.format!='JPEG' or im.size!=(1024,1024): raise ValueError(f'map format: {im.format}/{im.size}')
    return im.convert('RGB'), dict(member=item.filename,sha256=sha(b),size=list(im.size))
def finish(base, source):
    gray=source.convert('L').resize((512,512),Image.Resampling.LANCZOS)
    a=np.asarray(gray,dtype=np.float32)
    lo=np.asarray(gray.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)
    high=a-lo
    p=float(np.percentile(np.abs(high),95))
    if p<1: raise ValueError('insufficient measured fiber variation')
    tile=np.clip(high/p,-1,1)*0.065
    factor=1+np.concatenate([tile,tile],axis=1)
    orig=np.asarray(base.convert('RGBA'),dtype=np.uint8)
    out=orig.copy(); out[:,:,:3]=np.clip(np.rint(orig[:,:,:3]*factor[:,:,None]),0,255).astype(np.uint8)
    assert np.array_equal(orig[:,:,3],out[:,:,3])
    diff=np.abs(out[:,:,:3].astype(int)-orig[:,:,:3].astype(int))
    assert int(diff.max())<=17 and float(diff.mean())>0
    assert np.array_equal(out[:,:512],out[:,512:])
    return Image.fromarray(out),dict(max_rgb_delta=int(diff.max()),mean_rgb_delta=float(diff.mean()),detail_p95=p,alpha_exact=True,tile_repeat_exact=True)
def main(base_path,archive,out_path):
    p=pathlib.Path(out_path); p.mkdir(parents=True,exist_ok=False)
    base=Image.open(base_path).convert('RGBA'); assert base.size==(1024,512) and sha(base.tobytes())==BASE_PIXEL_SHA
    raw=pathlib.Path(archive).read_bytes(); assert len(raw)<=24_000_000
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert len(z.infolist())<=100 and sum(i.file_size for i in z.infolist())<=120_000_000 and z.testzip() is None
        color,meta=load_map(z,'_Color.jpg')
        normal,nmeta=load_map(z,'_NormalGL.jpg')
        rough,rmeta=load_map(z,'_Roughness.jpg')
    dark=Image.new('RGBA',(1024,512),(53,39,68,255))
    receipt=dict(scope='EXPLORATORY_MATERIAL_NOT_ADOPTED',source=SOURCE,license='CC0-1.0',license_url=LICENSE,archive_sha256=sha(raw),maps=[meta,nmeta,rmeta],source_technique='Photometric Stereo (provider listing)',base_pixel_sha256=BASE_PIXEL_SHA,outputs={},limitations=['Unregistered UV mapping; dark cloth color estimated','No final garment/face/body or physical scale approval','Normal and roughness recorded for later Blender use; not applied in VRoid'])
    for name,im in [('plaid_accent',base),('dark_pleat',dark)]:
        result,qa=finish(im,color); target=p/(name+'.png');result.save(target)
        assert Image.open(target).convert('RGBA').tobytes()==result.tobytes()
        receipt['outputs'][name]=dict(**qa,sha256=sha(target.read_bytes()),pixel_sha256=sha(result.tobytes()))
    preview=Image.new('RGB',(1024,560),(24,24,24));d=ImageDraw.Draw(preview)
    for x,im,label in [(0,base,'Authored plaid / control'),(512,Image.open(p/'plaid_accent.png'),'Measured fiber candidate')]:
        preview.paste(im.crop((0,0,512,512)).convert('RGB'),(x,32));d.text((x+10,10),label,fill='white')
    preview.save(p/'comparison.png')
    (p/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__': main(*sys.argv[1:])
