"""Render two downloaded, SHA-verified CC0 rock candidates without modifying source."""
import bpy,sys,argparse,json,hashlib,math
from pathlib import Path
from mathutils import Vector
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:]);source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((source/"source_provenance.json").read_text())
 results=[]
 for item in manifest["assets"]:
  assert item["status"]=="DOWNLOADED_UNREVIEWED"
  model=source/item["file"];assert sha(model)==item["sha256"]
  for dep in item["dependencies"]:
   assert sha(source/dep["file"])==dep["sha256"]
  bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
  bpy.ops.import_scene.gltf(filepath=str(model))
  meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
  assert meshes, item["id"]
  verts=sum(len(o.data.vertices) for o in meshes);faces=sum(len(o.data.polygons) for o in meshes)
  assert verts>100 and faces>100
  # Candidate inspection only: Workbench gives reliable mesh geometry preview.
  allpts=[o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
  lo=Vector([min(v[k] for v in allpts) for k in range(3)])
  hi=Vector([max(v[k] for v in allpts) for k in range(3)])
  center=(lo+hi)*.5;span=max(hi-lo)
  camera_data=bpy.data.cameras.new("QA_CAMERA");camera=bpy.data.objects.new("QA_CAMERA",camera_data);bpy.context.collection.objects.link(camera)
  camera.location=center+Vector((span*1.45,-span*1.7,span*1.2))
  direction=center-camera.location;camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
  camera_data.type="ORTHO";camera_data.ortho_scale=span*2.15
  scene=bpy.context.scene;scene.camera=camera
  scene.render.engine="BLENDER_WORKBENCH";scene.display.shading.light="STUDIO";scene.display.shading.color_type="MATERIAL";scene.display.shading.show_cavity=True
  scene.render.resolution_x=1100;scene.render.resolution_y=760;scene.render.resolution_percentage=100
  scene.render.image_settings.file_format="PNG";scene.render.filepath=str(out/(item["id"]+"_geometry_preview.png"))
  bpy.ops.render.render(write_still=True)
  results.append({"id":item["id"],"source_sha256":item["sha256"],"meshes":len(meshes),"vertices":verts,"faces":faces,"preview":Path(scene.render.filepath).name,"preview_sha256":sha(scene.render.filepath),"geometry_import":"PASS","PBR_visual_QA":"NOT_RUN","production_G2":"NOT_RUN"})
 (out/"candidate_geometry_report.json").write_text(json.dumps({"candidates":results,"G1":"BLOCKED","G2":"NOT_RUN","G3":"GLTF_IMPORT_AND_WORKBENCH_PREVIEW_PASS","G4":"NOT_RUN"},indent=2)+"\n")
 print("CC0_ROCK_GEOMETRY_PREVIEW_PASS",json.dumps(results),flush=True)
if __name__=="__main__":main()
