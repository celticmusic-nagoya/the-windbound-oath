"""Verify official CC0 source mesh against preserved stage, without editing either."""
import hashlib
import json
import pathlib
import sys
import zipfile
import bpy
import zstandard

archive, stage, out = map(pathlib.Path, sys.argv[sys.argv.index('--')+1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)=='811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515'
with zipfile.ZipFile(archive) as z:
    names=z.namelist();matches=[n for n in names if n.endswith('/human_base_meshes_bundle.blend')];assert len(matches)==1
    data=z.read(matches[0]);texts={n:z.read(n).decode('utf-8',errors='replace') for n in names if n.lower().endswith(('.txt','.md')) and z.getinfo(n).file_size<100000}
if not data.startswith(b'BLENDER'):
    data=zstandard.ZstdDecompressor().decompress(data,max_output_size=500_000_000)
assert hashlib.sha256(data).hexdigest()=='e5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a'
source=archive.parent/'verified_official_source.blend';source.write_bytes(data)
def signature(ob):
    coords=[[round(float(x),7) for x in ob.matrix_world@v.co] for v in ob.data.vertices]
    faces=[list(p.vertices) for p in ob.data.polygons]
    return hashlib.sha256(json.dumps([coords,faces],separators=(',',':')).encode()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
ob=bpy.data.objects['GEO-body_female_realistic'];original=signature(ob)
metadata={}
for owner in [ob,ob.data,*bpy.data.collections]:
    if owner.asset_data:
        meta=owner.asset_data
        metadata[owner.name]={key:str(getattr(meta,key,'')) for key in ['author','description','license','copyright']}
bpy.ops.wm.open_mainfile(filepath=str(stage),load_ui=False)
assert original==signature(bpy.data.objects['MORWEN_PROPORTION_STAGE_UNAPPROVED']),'stage differs from official source'
report={'status':'PASS_EXACT_TOPOLOGY_AND_COORDINATES','official_bundle_url':'https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip','official_license_listing':'https://www.blender.org/download/demo-files/#assets','license':'CC0 — Human Base Meshes (not other demo files)','official_archive_sha256':sha(archive),'official_blend_sha256':sha(source),'stage_sha256':sha(stage),'source_object':'GEO-body_female_realistic','geometry_signature':original,'asset_metadata':metadata,'archive_texts':texts,'stage_matches_official_geometry':True,'art_approval':False}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
