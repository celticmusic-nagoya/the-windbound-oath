"""Candidate-only GLB roundtrip QA; compare isolated imports and PBR node values."""
import bpy,sys,json,math
from pathlib import Path
source,exported,output=map(Path,sys.argv[sys.argv.index('--')+1:])
def material_info(m):
 p=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes and m.node_tree else None
 def value(key):
  if not p:return None
  v=p.inputs.get(key)
  if v is None:return None
  x=v.default_value
  return [round(float(y),6) for y in x] if hasattr(x,'__len__') else round(float(x),6)
 images=sorted({(n.image.name if n.image else '<missing>') for n in m.node_tree.nodes if n.type=='TEX_IMAGE'}) if m.use_nodes and m.node_tree else []
 return {'base_color':value('Base Color'),'metallic':value('Metallic'),'roughness':value('Roughness'),'alpha':value('Alpha'),'textures':images}
def inspect(path):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(path))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 materials={}
 for o in meshes:
  for m in o.data.materials:
   if m:materials[m.name]=material_info(m)
 return {'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
 'polygons':sum(len(o.data.polygons) for o in meshes),
 'materials':materials,'uv_layers':sum(len(o.data.uv_layers) for o in meshes),
 'has_normals':all(len(o.data.corner_normals)==len(o.data.loops) for o in meshes)}
a=inspect(source);z=inspect(exported)
geometry=all(a[k]==z[k] for k in ('meshes','vertices','polygons','uv_layers','has_normals')) and a['has_normals']
names=set(a['materials'])==set(z['materials'])
values=a['materials']==z['materials']
report={'source':a,'roundtrip':z,'geometry_check':'PASS' if geometry else 'FAIL',
'material_name_check':'PASS' if names else 'FAIL',
'pbr_material_value_check':'PASS' if values else 'FAIL',
'G3':'PARTIAL_PASS_NEEDS_DETAILED_TOPOLOGY_AND_TEXTURE_BYTE_QA' if geometry and values else 'FAIL',
'G1':'BLOCKED_CANONICAL_MATCH','G2':'NOT_RUN','G4':'NOT_RUN'}
output.write_text(json.dumps(report,indent=2)+'\n')
print('GLB_ROUNDTRIP_QA',json.dumps(report))
if not (geometry and values):raise SystemExit(1)
