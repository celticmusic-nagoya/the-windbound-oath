#!/usr/bin/env python3
"""Candidate Morwen bob: continuous quad shell plus separately editable swept fringe.

Replaces failed 33-ribbon visual approach; source stage remains immutable.
All geometry is provisional until independent comparison with canonical art.
"""
import argparse,hashlib,json,math,pathlib
import bpy
from mathutils import Vector

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def mesh_obj(name,verts,faces,coll,mat):
 me=bpy.data.meshes.new(name+"_geometry")
 me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);coll.objects.link(ob);me.materials.append(mat)
 for poly in me.polygons:poly.use_smooth=True
 ob["qa_status"]="UNAPPROVED_CANDIDATE"
 return ob

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--stage",required=True);p.add_argument("--output",required=True)
 a=p.parse_args();src=pathlib.Path(a.stage).resolve();out=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==out or out.is_relative_to(src):raise SystemExit("BLOCKED unsafe paths")
 original=sha(src)
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 body=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 if body is None or body.type!="MESH":raise SystemExit("BLOCKED missing body")
 points=[body.matrix_world@v.co for v in body.data.vertices]
 zmax=max(v.z for v in points);zmin=min(v.z for v in points);height=zmax-zmin
 band=[v for v in points if v.z>zmax-height*.115]
 if len(band)<20:raise SystemExit("BLOCKED head not detected")
 cx=(min(v.x for v in band)+max(v.x for v in band))/2
 cy=(min(v.y for v in band)+max(v.y for v in band))/2
 rx=(max(v.x for v in band)-min(v.x for v in band))/2
 ry=(max(v.y for v in band)-min(v.y for v in band))/2
 if min(rx,ry)<.015:raise SystemExit("BLOCKED implausible head")
 for o in bpy.data.objects:
  if o.name.startswith(("bob_guide_","fringe_guide_")):o.hide_render=True;o.hide_viewport=True
 coll=bpy.data.collections.new("MORWEN_BOB_SHELL_CANDIDATE_UNAPPROVED")
 bpy.context.scene.collection.children.link(coll)
 mat=bpy.data.materials.new("Morwen_bob_violet_PBR_CANDIDATE")
 mat.use_nodes=True
 bsdf=mat.node_tree.nodes.get("Principled BSDF")
 bsdf.inputs["Base Color"].default_value=(.14,.06,.24,1)
 bsdf.inputs["Roughness"].default_value=.47
 mat.diffuse_color=(.14,.06,.24,1)
 # One connected surface, 64 sectors x 15 rows. Front hem is elevated
 # to leave the face visible; back hem extends to the nape.
 n=64;rows=16;verts=[];faces=[]
 crown=zmax+height*.008
 for j in range(rows):
  u=j/(rows-1)
  for i in range(n):
   t=2*math.pi*i/n
   front=max(0,-math.sin(t))
   side=max(0,abs(math.cos(t))-.45)/.55
   # Soft hemispherical crown transitioning into a shaped bob silhouette.
   radial=(.04+.96*min(1,u*2.5))*(1+.035*math.cos(3*t))
   x=cx+rx*1.13*radial*math.cos(t)
   y=cy+ry*1.14*radial*math.sin(t)
   # crown -> temples -> hem, with a front face opening.
   hem=zmax-height*(.125-.072*front+.01*side)
   if u<.48:
    z=crown-height*.045*(u/.48)**1.7
   else:
    z=(crown-height*.045)*(1-(u-.48)/.52)+hem*((u-.48)/.52)
   # Natural uneven tips, no periodic sawtooth blocks.
   z+=height*.002*math.sin(5*t+.7)*u**5
   verts.append((x,y,z))
 for j in range(rows-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n
   faces.append((a,b,b+n,a+n))
 shell=mesh_obj("MORWEN_BOB_CONTINUOUS_SHELL_UNAPPROVED",verts,faces,coll,mat)
 thick=shell.modifiers.new("shell_thickness","SOLIDIFY");thick.thickness=.003
 # Asymmetric, swept forelock. Five independent tapered quad ribbons,
 # placed above the eyes; this is a detail layer, not the primary silhouette.
 strands=[]
 for i in range(5):
  verts=[];faces=[]
  for j in range(13):
   u=j/12
   x=cx+rx*(-.65+i*.27+.29*u)
   y=cy-ry*(.91+.23*math.sin(math.pi*u))
   z=zmax-height*(.015+.042*u+.006*i/5)
   w=rx*(.18-.11*u)*(1-.8*u**6)
   verts.extend([(x-w,y,z),(x+w,y,z)])
  for j in range(12):faces.append((2*j,2*j+1,2*j+3,2*j+2))
  ob=mesh_obj("MORWEN_SWEPT_FRINGE_%02d_UNAPPROVED"%i,verts,faces,coll,mat)
  mod=ob.modifiers.new("fringe_thickness","SOLIDIFY");mod.thickness=.002
  strands.append(ob.name)
 body["hair_shell_candidate"]=True
 body["hair_art_qa"]="NOT_RUN"
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(out),load_ui=False)
 shell=bpy.data.objects.get("MORWEN_BOB_CONTINUOUS_SHELL_UNAPPROVED")
 body=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 if shell is None or body is None or len(shell.data.vertices)!=n*rows:raise SystemExit("FAIL missing saved shell")
 camera=bpy.context.scene.camera
 if camera is None or camera.type!="CAMERA":raise SystemExit("BLOCKED camera missing")
 camera.data.type="ORTHO"
 scene=bpy.context.scene
 scene.render.resolution_x=768;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 coords=[body.matrix_world@v.co for v in body.data.vertices]
 lo=Vector(tuple(min(v[k] for v in coords) for k in range(3)))
 hi=Vector(tuple(max(v[k] for v in coords) for k in range(3)))
 center=(lo+hi)*.5
 camera.data.ortho_scale=max((hi.z-lo.z)*1.2,(hi.x-lo.x)*1.6,(hi.y-lo.y)*1.6)
 previews=[]
 for label,direction in (("front",(0,-1,0)),("back",(0,1,0)),("left",(-1,0,0)),("right",(1,0,0))):
  camera.location=center+Vector(direction)*max(hi-lo)*3
  camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
  png=out.parent/("morwen_bob_shell_"+label+".png")
  scene.render.filepath=str(png)
  bpy.ops.render.render(write_still=True)
  if not png.is_file() or png.stat().st_size<1000 or png.open("rb").read(8)!=bytes.fromhex("89504e470d0a1a0a"):
   raise SystemExit("FAIL invalid PNG "+str(png))
  previews.append({"view":label,"file":png.name,"sha256":sha(png)})
 if sha(src)!=original:raise SystemExit("FAIL source mutated")
 manifest={"status":"PASS_TECHNICAL_GENERATION_ONLY","approach":"continuous bob shell plus five swept forelocks",
  "shell_vertices":len(shell.data.vertices),"shell_faces":len(shell.data.polygons),
  "fringe_count":len(strands),"input_sha256":original,"output_sha256":sha(out),
  "source_unchanged":True,"art_qa":"NOT_RUN","game_qa":"NOT_RUN","previews":previews}
 (out.parent/"hair_shell_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
 print(json.dumps({"status":manifest["status"],"shell_vertices":manifest["shell_vertices"]}))
if __name__=="__main__":main()
