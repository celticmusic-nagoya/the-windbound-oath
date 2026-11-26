"""Exact read-only V13 native -> isolated GLB and interface measurements."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='c7abc4d59ea235be0aa785239a7b55563ad608afc9428fbd81207d282cd34691'
assert sha(src)==lock and bpy.app.version[:3]==(5,3,0)
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
bpy.context.view_layer.update()
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
assert len(visible)>300
names=['V3_village_reconstructed_patch','V8_west_grade','V9_east_grade','V10_perimeter_heightfield']
g=[bpy.data.objects[n] for n in names]
def report(o):
    v=[list(o.matrix_world@a.co) for a in o.data.vertices]
    o.data.calc_loop_triangles()
    return dict(name=o.name,vertices=len(v),triangles=len(o.data.loop_triangles),bounds=[[min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]])
terrain={}
for o in g:
    o.data.calc_loop_triangles()
    terrain[o.name]={'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(t.vertices) for t in o.data.loop_triangles]}
(out/'terrain_interfaces.json').write_text(json.dumps(terrain,separators=(',',':'))+'\n')
bpy.ops.object.select_all(action='DESELECT')
for o in visible:
    o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=visible[0]
p=out/'village_v13_SCENIC_EXPORT.glb'
# Direct export: procedural Blender nodes may not be reproduced; retain native as the visual master.
res=bpy.ops.export_scene.gltf(filepath=str(p.resolve()),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_cameras=False,export_lights=False,export_animations=False)
assert 'FINISHED' in res and p.stat().st_size>1000000 and sha(src)==lock
q={'status':'DIRECT_SCENIC_EXPORT_NOT_ADOPTED','source_sha256':lock,'blender':bpy.app.version_string,'mesh_objects':len(visible),'mesh_inventory':[report(o) for o in visible],'axes':'native X east Y north Z up; GLB X east Y up Z south','outputs':{f.name:sha(f) for f in out.iterdir() if f.is_file()},'limits':['Direct export, no baked procedural shader equivalence. Native source unchanged. Provisional local BU. No final placement or gameplay QA.']}
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
