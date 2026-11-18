"""Read-only Blender QA on saved replacement topology, exterior and bend keys."""
from pathlib import Path
import bpy,json,os
import numpy as np
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01'
source=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend';target=ROOT/'assets/candidates/morwen-rebuild-01/body-quad-v01/MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0];a=np.array([list(v.co) for v in o.data.vertices]);faces=[list(f.vertices) for f in o.data.polygons];uvs={layer.name:[tuple(x.uv) for x in layer.data] for layer in o.data.uv_layers};loopids=[list(f.loop_indices) for f in o.data.polygons]
bpy.ops.wm.open_mainfile(filepath=str(target),load_ui=False,use_scripts=False);o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0];m=o.data;vid=[x.value for x in m.attributes['RB_SRC_VID'].data];fid=[x.value for x in m.attributes['RB_SRC_FID'].data];pid=[x.value for x in m.attributes['RB_PATCH_ID'].data];vm={v:i for i,v in enumerate(vid)}
D=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-local-v01/local-edit.npz');protected=np.where(~D['free_mask'])[0];b=np.array([list(v.co) for v in m.vertices]);assert np.array_equal(a[protected],b[[vm[int(i)] for i in protected]])
retained=sum(v>=0 for v in vid);assert all(np.array_equal(a[v],b[i]) for i,v in enumerate(vid) if v>=0)
uv_checked=0;outside=0
for i,sid in enumerate(fid):
 if sid<0:continue
 outside+=1;face=m.polygons[i];assert [vid[v] for v in face.vertices]==faces[sid]
 for name,old_uv in uvs.items():
  new=m.uv_layers[name]
  assert [tuple(new.data[k].uv) for k in face.loop_indices]==[old_uv[k] for k in loopids[sid]]
  uv_checked+=1
assert outside==11753
assert m.shape_keys and len(m.shape_keys.key_blocks)==5
assert all(k.value==0 for k in m.shape_keys.key_blocks if k.name!='Basis')
assert np.array_equal(b,np.array([list(v.co) for v in m.shape_keys.key_blocks['Basis'].data]))
C=json.loads((Q/'candidate-mesh.json').read_text());assert vid==C['source_vertex_ids'];assert np.array_equal(b,np.array(C['local']))
world=np.array([list(o.matrix_world@v.co) for v in m.vertices]);assert np.allclose(world,np.array(C['world']),atol=1e-7,rtol=0)
report={'task':'MORWEN-QUAD-SAVED-MESH-QA','blender':bpy.app.version_string,'vertices':len(m.vertices),'faces':len(m.polygons),'protected_vertices_exact':len(protected),'all_retained_old_vertices_exact':retained,'exterior_faces_topology_exact':outside,'exterior_face_uv_layers_checked':uv_checked,'basis_matches_saved_rest_mesh':True,'saved_mesh_matches_correspondence_input':True,'all_diagnostic_keys_zero_at_save':True,'diagnostic_keys':[k.name for k in m.shape_keys.key_blocks],'finite':bool(np.isfinite(world).all()),'G3_preservation_screen':'PASS','G3_patch_acceptance':'FAIL','reason':'2 tracked warning regions remain; strict intersections and quad fold flags. Preservation is not acceptance.'}
output=Path(os.environ.get('MORWEN_QUAD_SAVED_QA_OUTPUT',str(Q/'saved-mesh-qa.json')));output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
