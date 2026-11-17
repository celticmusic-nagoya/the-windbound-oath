"""Bounded, non-destructive Blender render -> machine QA -> framing correction.

Candidate-only. This is NOT generative AI or independent artistic QA.
Usage: python morwen_render_qa_loop.py -- source.blend output_dir
"""
import bpy, sys, os, json, hashlib, math
from mathutils import Vector
from solve_morwen_framing import solve_framing
src,out=sys.argv[sys.argv.index("--")+1:][:2]
os.makedirs(out,exist_ok=True)
def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
initial=sha(src)
report={"input_sha256":initial,"blender_version":bpy.app.version_string,"method":"deterministic_camera_framing_only","max_attempts":2,"attempts":[],"art_qa":"NOT_RUN","game_qa":"NOT_RUN","status":"BLOCKED"}
try:
 bpy.ops.wm.open_mainfile(filepath=src)
 objects=[o for o in bpy.context.scene.objects if o.type=="MESH" and not o.hide_render]
 if not objects:raise RuntimeError("No renderable meshes")
 pts=[o.matrix_world@Vector(corner) for o in objects for corner in o.bound_box]
 mn=Vector(tuple(min(v[i] for v in pts) for i in range(3)))
 mx=Vector(tuple(max(v[i] for v in pts) for i in range(3)))
 center=(mn+mx)*0.5
 height=max(mx.z-mn.z,0.01)
 width=max(mx.x-mn.x,0.01)
 scene=bpy.context.scene
 scene.render.engine="BLENDER_WORKBENCH"
 scene.render.resolution_x=512
 scene.render.resolution_y=768
 scene.render.resolution_percentage=100
 scene.render.film_transparent=True
 scene.render.image_settings.file_format="PNG"
 scene.display.shading.light="STUDIO"
 scene.display.shading.color_type="MATERIAL"
 cam_data=bpy.data.cameras.new("QA_CAMERA_TEMP")
 cam=bpy.data.objects.new("QA_CAMERA_TEMP",cam_data)
 scene.collection.objects.link(cam)
 scene.camera=cam
 cam_data.type="ORTHO"
 cam.location=center+Vector((0,-max(height,width)*2,0))
 direction=center-cam.location
 cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
 # Fit BOTH projected axes using the actual portrait camera aspect ratio.
 inv=cam.rotation_euler.to_matrix().inverted()
 projected=[inv@(v-center) for v in pts]
 extent_x=max(v.x for v in projected)-min(v.x for v in projected)
 extent_y=max(v.y for v in projected)-min(v.y for v in projected)
 aspect=scene.render.resolution_x/scene.render.resolution_y
 scale=max(extent_y,extent_x/aspect)/0.82
 report["projected_bounds"]={"width":round(extent_x,6),"height":round(extent_y,6),"aspect":aspect}
 report["method"]="alpha_silhouette_recenter_and_two_axis_fit"
 for attempt in range(1,3):
  cam_data.ortho_scale=scale
  path=os.path.join(out,"MORWEN_QA_FRONT_%02d.png"%attempt)
  scene.render.filepath=path
  bpy.ops.render.render(write_still=True)
  im=bpy.data.images.load(path,check_existing=False)
  pixels=im.pixels[:]
  w,h=im.size
  # Sample alpha on a coarse 4px grid; bounds are a screening heuristic, not segmentation QA.
  hits=[(x,y) for y in range(0,h,4) for x in range(0,w,4) if pixels[(y*w+x)*4+3]>0.5]
  bpy.data.images.remove(im)
  if not hits:
   result={"attempt":attempt,"status":"FAIL_EMPTY","path":os.path.basename(path)}
   report["attempts"].append(result);break
  left,right=min(x for x,y in hits),max(x for x,y in hits)
  bottom,top=min(y for x,y in hits),max(y for x,y in hits)
  occupancy=(top-bottom+4)/h
  clipped=(left<=4 or right>=w-8 or bottom<=4 or top>=h-8)
  good=0.72<=occupancy<=0.93 and not clipped
  result={"attempt":attempt,"path":os.path.basename(path),"sha256":sha(path),"occupancy_y":round(occupancy,4),"alpha_bbox_sampled":[left,bottom,right,top],"clipped":clipped,"status":"PASS_TECHNICAL_FRAMING" if good else "FAIL_FRAMING"}
  report["attempts"].append(result)
  if good:
   report["status"]="PASS_TECHNICAL_FRAMING_ONLY";break
  if attempt==1:
   # Feasibility-checked one-time correction based on the actual alpha silhouette.
   observed_width=(right-left+4)/w
   observed_height=(top-bottom+4)/h
   solution=solve_framing(observed_width,observed_height)
   report["framing_solver"]=solution
   if solution["status"]!="FEASIBLE":
    report["status"]=solution["status"]
    break
   local_right=cam.rotation_euler.to_matrix()@Vector((1,0,0))
   local_up=cam.rotation_euler.to_matrix()@Vector((0,1,0))
   dx=((left+right)/2-(w-1)/2)/w*scale*aspect
   dy=((bottom+top)/2-(h-1)/2)/h*scale
   cam.location+=local_right*dx+local_up*dy
   scale/=solution["zoom"]
   report["correction_reason"]="feasibility_solver_and_alpha_centering"
   report["recenter_local"]=[round(dx,6),round(dy,6)]
 else:
  report["status"]="FAIL_MAX_ATTEMPTS"
 if report["status"]=="BLOCKED":report["status"]="FAIL_MAX_ATTEMPTS"
except Exception as exc:
 report["status"]="BLOCKED_EXCEPTION"
 report["error"]=str(exc)
finally:
 report["source_sha256_after"]=sha(src)
 report["source_unchanged"]=report["source_sha256_after"]==initial
 if not report["source_unchanged"]:report["status"]="FAIL_SOURCE_MUTATED"
 with open(os.path.join(out,"MORWEN_RENDER_QA_REPORT.json"),"w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({"status":report["status"],"attempts":report["attempts"],"source_unchanged":report["source_unchanged"]}))
if report["status"]!="PASS_TECHNICAL_FRAMING_ONLY":sys.exit(1)
