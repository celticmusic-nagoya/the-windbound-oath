#!/usr/bin/env python3
"""Isolated low-glare comparison; never changes the official CC0 .blend."""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector
NAMES=("GEO-body_female_stylized","GEO-body_female_realistic")
VIEWS={"front":(0,-1,0),"back":(0,1,0),"left":(-1,0,0),"right":(1,0,0)}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 src=pathlib.Path(a.source).resolve();out=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==out or src in out.parents or out in src.parents:raise SystemExit("BLOCKED unsafe paths")
 source_sha=sha(src);out.mkdir(parents=True,exist_ok=True)
 result={"status":"NOT_RUN","source_sha256":source_sha,"blender":bpy.app.version_string,"method":"neutral diffuse clay / low-glare orthographic","views":[],"art_qa":"NOT_RUN","canonical_match":"BLOCKED","approved":False}
 for name in NAMES:
  bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
  original=bpy.data.objects.get(name)
  if original is None or original.type!="MESH":raise SystemExit("BLOCKED missing "+name)
  coords=[original.matrix_world@v.co for v in original.data.vertices]
  low=Vector(tuple(min(v[i] for v in coords) for i in range(3)));high=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
  center=(low+high)*.5;size=high-low;mesh=original.data.copy();transform=original.matrix_world.copy()
  for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
  ob=bpy.data.objects.new(name+"_NEUTRAL_UNAPPROVED",mesh);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=transform
  mat=bpy.data.materials.new("low_glare_gray");mat.use_nodes=True
  bsdf=mat.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(.31,.33,.36,1)
  bsdf.inputs["Roughness"].default_value=1.0
  if "Metallic" in bsdf.inputs:bsdf.inputs["Metallic"].default_value=0
  mesh.materials.clear();mesh.materials.append(mat)
  for poly in mesh.polygons:poly.material_index=0
  sc=bpy.context.scene;sc.render.engine="BLENDER_EEVEE_NEXT";sc.render.resolution_x=512;sc.render.resolution_y=768
  sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGBA";sc.render.film_transparent=True
  sc.view_settings.view_transform="Standard";sc.view_settings.look="Medium High Contrast";sc.view_settings.exposure=-.5
  world=bpy.data.worlds.new("neutral_world");world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.15,.15,.15,1)
  world.node_tree.nodes["Background"].inputs["Strength"].default_value=.25;sc.world=world
  for label,offset,energy,diameter in (("key",(1.5,-2.0,2.5),110,4.0),("fill",(-1.5,-1.0,1.0),55,4.0),("rim",(0,2.0,2.0),85,4.0)):
   light=bpy.data.lights.new(label,"AREA");light.energy=energy;light.shape="DISK";light.size=diameter
   obj=bpy.data.objects.new(label,light);sc.collection.objects.link(obj);obj.location=center+Vector(offset)*max(size.z,1)
   obj.rotation_euler=(center-obj.location).to_track_quat("-Z","Y").to_euler()
  camdata=bpy.data.cameras.new("ortho");cam=bpy.data.objects.new("ortho",camdata);sc.collection.objects.link(cam);sc.camera=cam;camdata.type="ORTHO";camdata.ortho_scale=2.05
  for view,direction in VIEWS.items():
   cam.location=center+Vector(direction)*max(size)*3;cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
   png=out/(name+"_"+view+"_lowglare.png");sc.render.filepath=str(png);bpy.ops.render.render(write_still=True)
   if not png.is_file() or png.stat().st_size<1000 or png.open("rb").read(8)!=bytes.fromhex("89504e470d0a1a0a"):raise SystemExit("FAIL PNG "+png.name)
   result["views"].append({"mesh":name,"view":view,"file":png.name,"sha256":sha(png),"ortho_scale":2.05})
 if sha(src)!=source_sha:raise SystemExit("FAIL source changed")
 result["source_unchanged"]=True;result["status"]="PASS_DIAGNOSTIC_RENDER_ONLY"
 (out/"lowglare_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({"status":result["status"],"render_count":len(result["views"])}))
if __name__=="__main__":main()
