"""WORLD: normalized, isolated cliff macro-support topology experiment.

This is NOT a final art asset and does not encode approved metric scale.
Creates a continuous, watertight sculpting substrate, not a box blockout.
No scan geometry is modified. Normalized units are arbitrary local coordinates.
"""
import bpy,math,random,sys,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector

SEED=20261117
def h(path):
 x=hashlib.sha256()
 with open(path,"rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):x.update(chunk)
 return x.hexdigest()

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 for c in list(bpy.data.collections):
  if c.name=="Collection":c.name="LIND_TERRAIN"
 rng=random.Random(SEED)
 # Closed grid surface loft: x runs along coast, y is a landward cross-section,
 # z rises from wave-cut foot to the irregular inland top. This substrate has
 # a continuous physical back and underside. All units are non-metric.
 nx,ny=65,33
 def top(i,j):
  u=i/(nx-1);v=j/(ny-1)
  coast=0.12*math.sin(2*math.pi*u*1.7)+0.055*math.sin(2*math.pi*u*5.1+0.4)
  ridge=0.13*math.sin(2*math.pi*u*2.2+1.0)+0.05*math.sin(2*math.pi*u*7.3)
  cliff_height=1.0+ridge
  # x-z profile deliberately not a constant-height extrusion
  z=0.10+(cliff_height-0.10)*(v**0.31)
  z+=0.07*math.sin(u*18.0+v*9.0)*math.sin(math.pi*v)**2
  z+=0.035*math.sin(u*44+v*20)*math.sin(math.pi*v)**2
  y=1.25*v+coast*(1-v)+0.08*math.sin(u*13+v*5)*math.sin(math.pi*v)
  return (u*3.2-1.6,y,z)
 verts=[top(i,j) for i in range(nx) for j in range(ny)]
 top_faces=[]
 idx=lambda i,j:i*ny+j
 for i in range(nx-1):
  for j in range(ny-1):
   top_faces.append((idx(i,j),idx(i+1,j),idx(i+1,j+1),idx(i,j+1)))
 # Close all four sidewalls to a single shared bottom plane.
 n=len(verts)
 verts.extend((x,y,-0.24) for x,y,z in verts)
 faces=list(top_faces)
 faces.extend(tuple(reversed(tuple(n+k for k in f))) for f in top_faces)
 for i in range(nx-1):
  for j in (0,ny-1):
   a,b=idx(i,j),idx(i+1,j)
   faces.append((a,n+a,n+b,b) if j==0 else (b,n+b,n+a,a))
 for j in range(ny-1):
  for i in (0,nx-1):
   a,b=idx(i,j),idx(i,j+1)
   faces.append((b,n+b,n+a,a) if i==0 else (a,n+a,n+b,b))
 mesh=bpy.data.meshes.new("NORMALIZED_MACRO_SUPPORT_CLOSED");mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new("CLIFF_MACRO_SUPPORT_CANDIDATE_NOT_CANON",mesh)
 bpy.context.collection.objects.link(ob)
 # Correct face winding with bmesh recalc and check manifold/volume.
 bm=bmesh.new();bm.from_mesh(mesh)
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
 bm.to_mesh(mesh);bm.free()
 check=bmesh.new();check.from_mesh(mesh)
 boundary=sum(e.is_boundary for e in check.edges)
 nonmanifold=sum(not e.is_manifold for e in check.edges)
 volume=check.calc_volume(signed=False)
 faces_n=len(check.faces);verts_n=len(check.verts)
 check.free()
 if boundary or nonmanifold or volume<=0:raise RuntimeError(f"invalid macro support {boundary=} {nonmanifold=} {volume=}")
 mat=bpy.data.materials.new("Neutral stone sculpt substrate - candidate")
 mat.diffuse_color=(0.28,0.32,0.30,1)
 mat.use_nodes=True
 bs=mat.node_tree.nodes.get("Principled BSDF")
 bs.inputs["Base Color"].default_value=(0.31,0.35,0.32,1)
 bs.inputs["Roughness"].default_value=0.88
 ob.data.materials.append(mat)
 # Camera is an isolated QA view, NOT the approved game camera.
 bpy.ops.object.camera_add(location=(4.1,-5.5,3.1))
 cam=bpy.context.object;cam.name="QA_CAMERA_NON_CANON"
 cam.rotation_euler=(Vector((0,0.55,0.43))-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=4.9
 bpy.context.scene.camera=cam
 bpy.ops.object.light_add(type="AREA",location=(-2.0,-2.4,4.0))
 light=bpy.context.object;light.name="QA_AREA_NON_CANON";light.data.energy=650;light.data.shape="DISK";light.data.size=5
 scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH"
 scene.display.shading.light="STUDIO"
 scene.display.shading.color_type="MATERIAL"
 scene.display.shading.show_cavity=True
 scene.display.shading.cavity_type="BOTH"
 print("GEOMETRY_CLOSED",verts_n,faces_n,boundary,nonmanifold,volume,flush=True)
 scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 scene.world.color=(0.20,0.20,0.20)
 scene.render.image_settings.file_format="PNG"
 scene.render.filepath=str(out/"macro_support_clay.png")
 blend=out/"macro_support_candidate.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 print("BLEND_CHECKPOINT_SAVED",flush=True)
 print("RENDER_START_WORKBENCH",flush=True)
 bpy.ops.render.render(write_still=True)
 print("RENDER_FINISHED_WORKBENCH",flush=True)
 print("RENDER_COMPLETE_MODEL_ALREADY_SAVED",flush=True)
 metrics={"method":"AUTHORED_NORMALIZED_CONNECTED_MACRO_SUPPORT","seed":SEED,"units":"NORMALIZED_NON_METRIC","approved_world_scale":None,"approved_camera":None,
 "render_engine":"BLENDER_WORKBENCH","source_scan_used":False,"source_scan_embedded":False,"production_ready":False,
 "vertices":verts_n,"faces":faces_n,"boundary_edges":boundary,"nonmanifold_edges":nonmanifold,"closed_volume":volume,
 "G1":"BLOCKED","G2":"NOT_RUN","G3":"PASS_TOPOLOGY_ONLY","G4":"NOT_RUN",
 "outputs":{p.name:h(p) for p in (out/"macro_support_clay.png",blend)}}
 (out/"macro_support_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
 print("MACRO_SUPPORT_QA",json.dumps({k:metrics[k] for k in ("vertices","faces","boundary_edges","nonmanifold_edges","closed_volume")}))
if __name__=="__main__":main()
