"""UV-independent jersey material candidate. No native mapping or geometry claim."""
import hashlib,io,json,sys,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter

def sha(b): return hashlib.sha256(b).hexdigest()
def build(src,out):
    raw=Path(src).read_bytes()
    if sha(raw)!='9a904f93c5514043fbd5d7136715d0a80d7af28ffcb588a351f1c8f5265c0426': raise ValueError('archive digest mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None: raise ValueError('CRC')
        receipt=json.loads(z.read('receipt.json')); assert receipt['license']=='CC0'
        source=receipt['assets']['cotton_jersey']; data={}
        for key,ext in [('diffuse','jpg'),('normal','png'),('rough','jpg')]:
            b=z.read('cotton_jersey/'+key+'.'+ext); assert sha(b)==source['maps'][key]['sha256']; data[key]=b
    a=np.asarray(Image.open(io.BytesIO(data['diffuse'])).convert('RGB')); assert a.shape==(1025,1024,3)
    lum=Image.fromarray(a).convert('L'); l=np.asarray(lum,dtype=float); low=np.asarray(lum.filter(ImageFilter.GaussianBlur(12)),dtype=float)
    # Discard broad source colour and lighting, retain only restrained local weave residual.
    delta=np.clip((l-low)*.65,-8,8); delta-=np.median(delta)
    out=Path(out); out.mkdir(exist_ok=False)
    maps={}
    for name,color in [('sock-basecolor',[75,49,61]),('cuff-basecolor',[48,33,43])]:
        rgb=np.clip(np.rint(np.array(color)+delta[...,None]),0,255).astype(np.uint8); p=out/(name+'.png'); Image.fromarray(rgb).save(p); assert np.array_equal(np.asarray(Image.open(p)),rgb)
        maps[p.name]={'sha256':sha(p.read_bytes()),'median_rgb':np.median(rgb,axis=(0,1)).tolist(),'shape':list(rgb.shape)}
    for key,name in [('normal','jersey-normal-gl.png'),('rough','jersey-roughness.jpg')]:
        p=out/name; p.write_bytes(data[key]); assert sha(p.read_bytes())==source['maps'][key]['sha256']; maps[name]={'sha256':sha(p.read_bytes()),'exact_source_copy':True}
    result={'scope':'UV_INDEPENDENT_MATERIAL_CANDIDATE_NOT_ADOPTED','source_archive_sha256':sha(raw),'source':'https://polyhaven.com/a/cotton_jersey','license':'CC0','maps':maps,'basecolor_note':'Artist-selected muted violet-brown; high-pass weave only, no deliberate baked directional lighting. Not physical reflectance. Cuff and sock share trial microstructure.','normal_note':'Exact original OpenGL normal map; intensity and UV scale not qualified.','roughness_note':'Exact original roughness file; linear sampling in engine.','native_UV':'NOT_RUN','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': build(sys.argv[1],sys.argv[2])
