#!/usr/bin/env python3
"""Create a noncanonical, editable first-pass Morwen body candidate from verified CC0 geometry.
This is an actual deformed mesh, NOT a finished character or approved anatomy.
"""
import argparse,hashlib,json,pathlib,math
import bpy
from mathutils import Vector
SOURCE_NAME="GEO-body_female_realistic"
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def smooth(a,b,z):
 t=max(0.,min(1.,(z-a)/(b-a)))
 return t*t*(3-2*t)
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--output",required=True);p.add_argument("--renders",required=True);a=p.parse_args()
 src=pathlib.Path(a.source).resolve();dst=pathlib.Path(a.output).resolve();renders=pathlib.Path(a.renders).resolve()
 if not src.is_file() or dst==src or src in dst.parents or dst in src.parents:raise SystemExit("BLOCKED unsafe source/output")
 src_sha=sha(src);bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 original=bpy.data.objects.get(SOURCE_NAME)
 if original is None or original.type!="MESH":raise SystemExit("BLOCKED source missing")
 original_coords=[original.matrix_world@v.co for v in original.data.vertices]
 low=Vector(tuple(min(v[i] for v in original_coords) for i in range(3)));high=Vector(tuple(max(v[i] for v in original_coords) for i in range(3)))
 height=high.z-low.z;cx=(low.x+high.x)*.5;cy=(low.y+high.y)*.5
 # Explicit first-pass shape decisions. Smooth deformation retains original topology.
 # No head/chin landmarks are claimed; vertical regions are approximate body zones.
 mesh=original.data.copy();original_transform=original.matrix_world.copy()
 for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
 obj=bpy.data.objects.new("MORWEN_BODY_CANDIDATE_01_UNAPPROVED",mesh);bpy.context.scene.collection.objects.link(obj)
 obj.matrix_world=original_transform
 inv=obj.matrix_world.inverted()
 changed=0
 for vert in mesh.vertices:
  pos=obj.matrix_world@vert.co
  z=(pos.z-low.z)/height
  # Shoulder taper, subtle waist shaping, preserve head size until reviewed.
  shoulder=math.exp(-((z-.79)/.075)**2)
  waist=math.exp(-((z-.59)/.07)**2)
  hip=math.exp(-((z-.49)/.075)**2)
  leg=math.exp(-((z-.29)/.18)**2)
  sx=1.0-.055*shoulder-.065*waist+.012*hip-.015*leg
  sy=1.0-.025*shoulder-.035*waist+.008*hip
  new=Vector((cx+(pos.x-cx)*sx,cy+(pos.y-cy)*sy,pos.z))
  if (new-pos).length>1e-7:changed+=1
  vert.co=inv@new
 mesh.update()
 mat=bpy.data.materials.new("Morwen_candidate_neutral_clay");mat.use_nodes=True
 bsdf=mat.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(.34,.36,.4,1);bsdf.inputs["Roughness"].default_value=1
 mesh.materials.clear();mesh.materials.append(mat)
 for face in mesh.polygons:face.material_index=0
 sc=bpy.context.scene;sc.render.engine="BLENDER_EEVEE_NEXT";sc.render.resolution_x=512;sc.render.resolution_y=768
 sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGBA";sc.render.film_transparent=True
 sc.view_settings.view_transform="Standard";sc.view_settings.look="Medium High Contrast";sc.view_settings.exposure=-.5
 world=bpy.data.worlds.new("neutral_review_world");world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.15,.15,.15,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.25;sc.world=world
 center=(low+high)*.5
 for label,offset,energy in (("key",(1.5,-2,2.5),110),("fill",(-1.5,-1,1),55),("rim",(0,2,2),85)):
  light=bpy.data.lights.new(label,"AREA");light.energy=energy;light.shape="DISK";light.size=4
  light_obj=bpy.data.objects.new(label,light);sc.collection.objects.link(light_obj)
  light_obj.location=center+Vector(offset)*height;light_obj.rotation_euler=(center-light_obj.location).to_track_quat("-Z","Y").to_euler()
 camera_data=bpy.data.cameras.new("fixed_orthographic");camera=bpy.data.objects.new("fixed_orthographic",camera_data);sc.collection.objects.link(camera)
 sc.camera=camera;camera_data.type="ORTHO";camera_data.ortho_scale=2.05
 renders.mkdir(parents=True,exist_ok=True)
 paths=[]
 for view,direction in (("front",(0,-1,0)),("back",(0,1,0)),("left",(-1,0,0)),("right",(1,0,0))):
  camera.location=center+Vector(direction)*height*3;camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
  png=renders/("MORWEN_BODY_CANDIDATE_01_"+view+".png");sc.render.filepath=str(png);bpy.ops.render.render(write_still=True)
  if not png.exists() or png.stat().st_size<1000:raise SystemExit("FAIL missing render "+view)
  paths.append({"view":view,"file":png.name,"sha256":sha(png)})
 dst.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(dst))
 if sha(src)!=src_sha:raise SystemExit("FAIL source mutated")
 report={"status":"PASS_EDITABLE_DIAGNOSTIC_CANDIDATE_ONLY","candidate_sha256":sha(dst),"source_sha256":src_sha,"source_unchanged":True,
         "source_mesh":SOURCE_NAME,"candidate_mesh":obj.name,"original_vertex_count":len(original_coords),"candidate_vertex_count":len(mesh.vertices),
         "deformed_vertex_count":changed,"params":{"shoulder_x":-.055,"waist_x":-.065,"hip_x":.012,"leg_x":-.015},
         "views":paths,"canonical_match":"BLOCKED","head_ratio":"BLOCKED","art_qa":"NOT_RUN","rig_qa":"NOT_RUN","approved":False}
 (renders/"candidate_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"vertices":len(mesh.vertices),"deformed":changed}))
if __name__=="__main__":main()
