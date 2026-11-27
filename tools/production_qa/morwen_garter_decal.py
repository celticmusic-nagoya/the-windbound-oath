"""Projected right-leg accessory trial. Not a UV atlas or measured 3D shape."""
import hashlib, io, json, sys, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def sha(b): return hashlib.sha256(b).hexdigest()
def build(source,out):
    raw=Path(source).read_bytes()
    assert sha(raw)=='a290131b16f8c61ee32d30125e438782ab59e36ffa2ce9c132685cefa71016bc'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        ref=z.read('assets/companions/morwen/master/morwen-full-body-v3.png')
        assert sha(ref)=='96a88e1deb86734fc18b5d762bad6d5c33b9a481cdbf76d45d954e92a875f990'
        assert Image.open(io.BytesIO(ref)).size==(1024,1536)
    # 16 raster pixels per reference projection unit. No conversion to mm.
    k=16; size=(32*k,80*k)
    def blank(): return Image.new('L',size)
    def poly(mask,pts): ImageDraw.Draw(mask).polygon([(round(x*k),round(y*k)) for x,y in pts],fill=255)
    def ellipse(mask,box): ImageDraw.Draw(mask).ellipse(tuple(round(x*k) for x in box),fill=255)
    strap=blank(); metal=blank(); inset=blank()
    # Visible strap only; upper termination and rear fastening unresolved.
    poly(strap,[(8.5,3),(23.5,3),(23.5,45),(21,49),(11,49),(8.5,45)])
    # 13 x 28 projected-unit clasp; tapered lower tip and recessed center.
    poly(metal,[(9.5,45),(22.5,45),(22.5,49),(21,50),(21.5,58),(21,63),(19.5,65.5),(17.5,67),(16.8,71.5),(16,73),(15.2,71.5),(14.5,67),(12.5,65.5),(11,63),(10.5,58),(11,50),(9.5,49)])
    ellipse(inset,(12.2,50.5,19.8,65.8))
    # One visible strap rivet and two clasp pins, not a full fastening design.
    ellipse(metal,(14.5,25.5,17.5,28.5)); ellipse(metal,(10.1,46.5,13.1,49.5)); ellipse(metal,(18.9,46.5,21.9,49.5))
    s,m,i=[np.asarray(v)>0 for v in (strap,metal,inset)]; m &= ~i
    center=blank(); ellipse(center,(14,54,18,62.5)); m |= np.asarray(center)>0
    coverage=s|m|i; leather=(s|i)&~m
    rgba=np.zeros((size[1],size[0],4),np.uint8); rgba[leather,:3]=[51,35,45]; rgba[m,:3]=[205,158,108]; rgba[coverage,3]=255
    # Metalness and roughness are trial parameters, not measured material values.
    metallic=np.zeros(coverage.shape,np.uint8); metallic[m]=255
    rough=np.zeros(coverage.shape,np.uint8); rough[leather]=179; rough[m]=94
    out=Path(out); out.mkdir(exist_ok=False)
    maps={}
    for name,a in [('garter-basecolor',rgba),('garter-coverage',coverage.astype(np.uint8)*255),('garter-metallic',metallic),('garter-roughness',rough)]:
        p=out/(name+'.png'); Image.fromarray(a).save(p); assert np.array_equal(np.asarray(Image.open(p)),a); maps[p.name]=sha(p.read_bytes())
    assert not np.any(metallic[~coverage]); assert np.all(rgba[~coverage]==0); assert np.array_equal(rgba[:,:,3],coverage.astype(np.uint8)*255)
    report={'scope':'PROJECTED_DECAL_TRIAL_NOT_ADOPTED','source_archive_sha256':sha(raw),'reference_sha256':sha(ref),'landmark_blob':'16ff434c1a4dc3dabcddaa1e0fbf78bec72b3ffb','size':list(size),'raster_px_per_projected_unit':k,'strap_width_units':15,'clasp_width_height_units':[13,28],'shape_note':'artist-authored polygon approximation of visible silhouette; not traced pixels, native UV or physical geometry','material_note':'flat base colors; trial roughness and metallic only; no baked directional lighting','right_only':True,'D4':'NOT_RUN','native_fit':'NOT_RUN','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN','maps':maps}
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
if __name__=='__main__': build(sys.argv[1],sys.argv[2])
