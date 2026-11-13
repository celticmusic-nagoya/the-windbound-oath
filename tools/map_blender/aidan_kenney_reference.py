"""CC0 Kenney reference assembly, not an approved Aidan house asset.
Usage: blender -b --python tools/map_blender/aidan_kenney_reference.py -- /path/to/aidan_kenney_assembly_audit.zip /path/to/output
"""
import bpy, sys, zipfile, pathlib, tempfile, json, hashlib
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)!=2: raise SystemExit('Expected ZIP and output directory')
archive=pathlib.Path(args[0]);out=pathlib.Path(args[1]);out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None,'Invalid ZIP'
 names=z.namelist()
 assert all(not n.startswith('/') and '..' not in pathlib.PurePosixPath(n).parts for n in names)
 assert 'LICENSE_KENNEY.txt' in names
 license_text=z.read('LICENSE_KENNEY.txt').decode('utf8','replace')
 assert 'CC0' in license_text
 model_names=sorted(n for n in names if n.startswith('models/') and n.endswith('.glb'))
 assert len(model_names)>=12,'Expected 12 models'
 with tempfile.TemporaryDirectory() as temp:
  z.extractall(temp)
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  results=[]
  for index,name in enumerate(model_names):
   file=pathlib.Path(temp)/name
   before=set(bpy.data.objects)
   bpy.ops.import_scene.gltf(filepath=str(file))
   added=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
   assert added,'No mesh in '+name
   for ob in added:
    ob.location.x+=(index%4)*3.0
    ob.location.y+=(index//4)*3.0
   results.append({'name':name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'meshes':len(added)})
  bpy.ops.wm.save_as_mainfile(filepath=str(out/'kenney_reference.blend'))
  (out/'manifest.json').write_text(json.dumps({'status':'REFERENCE_ONLY','license':'CC0','parts':results},indent=2),encoding='utf8')
  print('PASS: imported',len(results),'reference GLBs')
