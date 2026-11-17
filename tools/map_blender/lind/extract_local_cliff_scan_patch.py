"""Non-destructive local source-scan patch extraction for later artist-led retopology.

Preserves original positions and UVs. Does not claim the cropped mesh is a
watertight, optimized, topology-rebuilt or game-ready asset.
"""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--out",required=True)
 args=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(args.out).resolve()
 gltf=out/"sources/coastal_cliff_04/coastal_cliff_04_1k.gltf"
 assert sha(gltf)=="645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11"
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(gltf))
 source=[o for o in bpy.context.scene.objects if o.type=="MESH"]
 assert len(source)==1
 source=source[0];source.name="SOURCE_SCAN_IMMUTABLE"
 mesh=source.data
 assert len(mesh.polygons)>500000 and mesh.uv_layers.active
 # Deterministic, surface-density-based local region: choose a well-populated
 # elevated grid cell, not a fixed location assumed to contain usable rock.
 bins={}
 for poly in mesh.polygons:
  c=poly.center
  if c.z<2.0:continue
  key=(math.floor(c.x/5),math.floor(c.y/5))
  bins[key]=bins.get(key,0)+1
 if not bins:raise RuntimeError("No elevated source polygons; do not invent patch")
 key=max(sorted(bins),key=lambda k:bins[k])
 center=Vector(((key[0]+.5)*5,(key[1]+.5)*5,0))
 selected=[]
 for poly in mesh.polygons:
  c=poly.center
  if abs(c.x-center.x)<=3.0 and abs(c.y-center.y)<=3.0 and c.z>=1.0:
   selected.append(poly)
 if len(selected)<3000:raise RuntimeError("Local patch too sparse")
 # Preserve topology and UV by copying the original indexed loops exactly.
 vertex_map={}
 verts=[]
 faces=[]
 uv_per_face=[]
 old_uv=mesh.uv_layers.active.data
 for poly in selected:
  face=[];uv=[]
  for li in poly.loop_indices:
   old=mesh.loops[li].vertex_index
   if old not in vertex_map:
    vertex_map[old]=len(verts)
    verts.append(tuple(mesh.vertices[old].co))
   face.append(vertex_map[old])
   uv.append(tuple(old_uv[li].uv))
  faces.append(face);uv_per_face.append(uv)
 new=bpy.data.meshes.new("LOCAL_PATCH_ORIGINAL_TOPOLOGY")
 new.from_pydata(verts,[],faces);new.update()
 new.uv_layers.new(name="PUBLISHER_UV_UNCHANGED")
 for face,uvs in zip(new.polygons,uv_per_face):
  for li,uv in zip(face.loop_indices,uvs):
   new.uv_layers.active.data[li].uv=uv
 patch=bpy.data.objects.new("LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY",new)
 bpy.context.collection.objects.link(patch)
 # Assign original source PBR material without rewriting publisher textures.
 for mat in mesh.materials:new.materials.append(mat)
 source.hide_render=True
 # Record topology of the selected *open* patch and source-to-patch UV fidelity.
 edge_counts={}
 for poly in new.polygons:
  v=list(poly.vertices)
  for i,a in enumerate(v):
   b=v[(i+1)%len(v)]
   e=(min(a,b),max(a,b))
   edge_counts[e]=edge_counts.get(e,0)+1
 open_edges=sum(n==1 for n in edge_counts.values())
 nonmanifold=sum(n>2 for n in edge_counts.values())
 bounds=[patch.matrix_world@Vector(c) for c in patch.bound_box]
 center3=sum(bounds,Vector())/8
 span=max(max(p[i] for p in bounds)-min(p[i] for p in bounds) for i in range(3))
 scene=bpy.context.scene
 scene.render.engine="BLENDER_EEVEE"
 scene.render.resolution_x=1200;scene.render.resolution_y=800
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 world=bpy.data.worlds.new("PATCH_QA_WORLD");world.use_nodes=True;scene.world=world
 world.node_tree.nodes["Background"].inputs["Color"].default_value=(.65,.70,.74,1)
 world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
 camd=bpy.data.cameras.new("PATCH_QA_CAMERA");camd.type="ORTHO";camd.ortho_scale=span*1.5
 cam=bpy.data.objects.new("PATCH_QA_CAMERA",camd);bpy.context.collection.objects.link(cam)
 cam.location=center3+Vector((span*.6,-span*1.5,span*.45))
 cam.rotation_euler=(center3-cam.location).to_track_quat("-Z","Y").to_euler()
 scene.camera=cam
 ld=bpy.data.lights.new("PATCH_AREA","AREA");lo=bpy.data.objects.new("PATCH_AREA",ld)
 bpy.context.collection.objects.link(lo)
 lo.location=center3+Vector((-span*.4,-span*.6,span*.7))
 lo.rotation_euler=(center3-lo.location).to_track_quat("-Z","Y").to_euler()
 ld.energy=3500;ld.size=max(2,span*.3)
 png=out/"local_source_patch_pbr.png"
 scene.render.filepath=str(png)
 bpy.ops.render.render(write_still=True)
 bpy.ops.file.pack_all()
 blend=out/"local_source_patch_reference.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 result={"source_gltf_sha256":sha(gltf),"selection_grid_cell":list(key),
 "selection_cell_count":bins[key],"selection_faces":len(faces),
 "patch_vertices":len(verts),"open_boundary_edges":open_edges,
 "nonmanifold_edges":nonmanifold,"uv_source":"publisher UV loop values preserved",
 "source_mesh_status":"UNCHANGED","patch_status":"UNOPTIMIZED_REFERENCE_ONLY",
 "bake_status":"NOT_RUN","retopology_status":"NOT_RUN",
 "outputs":{x.name:sha(x) for x in [png,blend]},
 "G1":"BLOCKED","G2":"NOT_RUN_INDEPENDENT","G3":"OPEN_PATCH_REFERENCE_ONLY","G4":"NOT_RUN"}
 (out/"local_patch_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
 print("LOCAL_SOURCE_PATCH_COMPLETE",json.dumps({"faces":len(faces),"open_edges":open_edges,"nonmanifold":nonmanifold}))
if __name__=="__main__":main()
