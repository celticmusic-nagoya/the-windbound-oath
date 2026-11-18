"""Replace only selected interior faces/vertices; preserve stable exterior IDs/UVs."""
from pathlib import Path
import json,bpy,bmesh
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01';OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-quad-v01'
R=json.loads((Q/'quad-patch-recipe.json').read_text());D=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-local-v01/local-edit.npz');rest=D['original_source_world'];free=D['free_mask']
p=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend'
bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False,load_ui=False);o=bpy.data.objects['MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED'];inv=o.matrix_world.inverted()
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
vl=bm.verts.layers.int.new('RB_SRC_VID');fl=bm.faces.layers.int.new('RB_SRC_FID');pl=bm.faces.layers.int.new('RB_PATCH_ID')
rx=bm.verts.layers.float.new('RB_REST_X');ry=bm.verts.layers.float.new('RB_REST_Y');rz=bm.verts.layers.float.new('RB_REST_Z')
for i,v in enumerate(bm.verts):v[vl]=i;v[rx],v[ry],v[rz]=map(float,rest[i])
for i,f in enumerate(bm.faces):f[fl]=i;f[pl]=0
V={v[vl]:v for v in bm.verts};retired=set(R['retired_source_faces']);dead=[f for f in bm.faces if f[fl] in retired]
assert all(all(free[v[vl]] for v in f.verts) for f in dead)
bmesh.ops.delete(bm,geom=dead,context='FACES_ONLY')
for e in list(bm.edges):
 if not e.link_faces:bm.edges.remove(e)
removed_vertices=sorted({i for p in R['patches'] for i in p['retired_interior_vertices']})
for i in removed_vertices:
 assert not V[i].link_faces
 bm.verts.remove(V.pop(i))
uvlayers=list(bm.loops.layers.uv.values());patchuv=bm.loops.layers.uv.new('RB_PATCH_UV')
face_new_id=-1
for patchid,p in enumerate(R['patches'],1):
 pv=[]
 for sid,xyz,rxyz in zip(p['new_source_vertex_ids'],p['new_world'],p['new_rest_world']):
  if sid>=0:v=V[sid]
  else:
   v=bm.verts.new(inv@Vector(xyz));v[vl]=sid;v[rx],v[ry],v[rz]=map(float,rxyz);V[sid]=v
  pv.append(v)
 for face in p['new_faces']:
  f=bm.faces.new([pv[i] for i in face]);f[fl]=face_new_id;face_new_id-=1;f[pl]=patchid;f.material_index=0;f.smooth=False
  for loop,i in zip(f.loops,face):
   uv=np.array(p['new_uv'][i])*.5+.5
   loop[patchuv].uv=uv
   for layer in uvlayers:loop[layer].uv=uv
bm.normal_update();bm.to_mesh(o.data);bm.free();o.data.update();o.name='MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED'
o['method']='Boundary-conforming topology replacement; anatomical rest rails and patellar controls'
o['parent']='body-local-v01 retained unchanged'
o['art_status']='UNAPPROVED_REQUIRES_INDEPENDENT_QA'
o['production_rig']='NOT_IMPLEMENTED; diagnostic bend keys only'
scene=bpy.context.scene;scene.camera=bpy.data.objects['SOURCE_REVIEW_front'];scene.render.resolution_x=512;scene.render.resolution_y=768
OUT.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
blend=OUT/'MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
# Export actual stored coordinates + stable identifiers for post-retopo correspondence.
mesh=o.data;sid=mesh.attributes['RB_SRC_VID'];fid=mesh.attributes['RB_SRC_FID'];pid=mesh.attributes['RB_PATCH_ID']
record={'world':[list(o.matrix_world@v.co) for v in mesh.vertices],'local':[list(v.co) for v in mesh.vertices],'source_vertex_ids':[a.value for a in sid.data],'faces':[list(f.vertices) for f in mesh.polygons],'source_face_ids':[a.value for a in fid.data],'patch_ids':[a.value for a in pid.data]}
(Q/'candidate-mesh.json').write_text(json.dumps(record,separators=(',',':'))+'\n')
print('NEW_QUAD_PATCH_MESH_SAVED',len(mesh.vertices),len(mesh.polygons),'new faces',-face_new_id-1,'retired faces',len(retired))
