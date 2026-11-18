"""Technical GLB roundtrip QA; candidate-only, no canonical approval."""
import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
source,exported,output=map(Path,args)
def inspect(path):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(path))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 return {'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
 'polygons':sum(len(o.data.polygons) for o in meshes),
 'materials':sorted({m.name for o in meshes for m in o.data.materials if m}),
 'uv_layers':sum(len(o.data.uv_layers) for o in meshes),
 'has_normals':all(len(o.data.corner_normals)==len(o.data.loops) for o in meshes)}
a=inspect(source);z=inspect(exported)
# GLB import/export may triangulate and rename; report counts without claiming exact identity.
passed=a['meshes']==z['meshes'] and a['vertices']==z['vertices'] and a['uv_layers']==z['uv_layers'] and a['has_normals'] and z['has_normals']
report={'source':a,'roundtrip':z,'mesh_vertex_uv_normal_check':'PASS' if passed else 'FAIL',
'material_name_check':'PASS' if a['materials']==z['materials'] else 'REVIEW',
'G3':'PARTIAL_PASS_NOT_FULL_TOPOLOGY_OR_MATERIAL_EQUIVALENCE' if passed else 'FAIL',
'G1':'BLOCKED_CANONICAL_MATCH','G2':'NOT_RUN','G4':'NOT_RUN'}
output.write_text(json.dumps(report,indent=2)+'\n')
print('GLB_ROUNDTRIP_QA',json.dumps(report))
if not passed:raise SystemExit(1)
