"""Export Aidan candidate to glTF for the isolated development viewer.
Usage: blender -b -t 2 --python tools/dev-camera/export_aidan_glb.py
Does not edit canonical assets or game runtime.
"""
import bpy,os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'map_blender'))
from aidan_house_master_v2 import build
out=Path(os.environ.get('AIDAN_GLTF_OUTPUT','/tmp/aidan-dev-camera'))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
data=build()
# Export object transforms and named collections; Preserve Blender Z-up for the viewer's Z-up camera.
path=out/'aidan_house_master_v2.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=False,export_apply=True,export_cameras=False,export_lights=False)
assert path.exists() and path.stat().st_size>1000
report={'status':'DEVELOPMENT_VIEWER_ONLY_NOT_ART_APPROVED','source':'aidan_house_master_v2.py','glb':path.name,'bytes':path.stat().st_size,'geometry':data}
(out/'manifest.json').write_text(json.dumps(report,indent=2))
print('DEV_CAMERA_EXPORT='+json.dumps(report))
