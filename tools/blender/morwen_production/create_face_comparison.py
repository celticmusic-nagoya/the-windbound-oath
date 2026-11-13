"""Create review-only comparison of immutable canonical artwork and actual VRoid renders."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path("tools/blender/production_mesh_08/references")
out=Path("render_output/morwen_vroid_review")
views=[("front","7809.png"),("right","7807.png"),("left","7808.png")]
checks={"front":"b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed","right":"9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737","left":"69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa"}
# Each column contains original full-body reference (left) and unmodified head render (right).
# This is an alignment aid, NOT an automatically registered landmark comparison.
tile_w,tile_h=384,768
canvas=bpy.data.images.new("MORWEN_REVIEW_ONLY",width=tile_w*6,height=tile_h,alpha=True)
pixels=[0.14,0.14,0.16,1.0]*(tile_w*6*tile_h)
def blit(src,col,crop=None):
 w,h=src.size
 rgba=list(src.pixels[:])
 # crop is (x0,y0,x1,y1) in Blender bottom-origin image pixels
 x0,y0,x1,y1=crop if crop else (0,0,w,h)
 assert 0<=x0<x1<=w and 0<=y0<y1<=h
 cw,ch=x1-x0,y1-y0
 scale=min(tile_w/cw,tile_h/ch)
 nw=max(1,int(cw*scale));nh=max(1,int(ch*scale))
 for y in range(nh):
  sy=y0+min(ch-1,int(y/scale))
  for x in range(nw):
   sx=x0+min(cw-1,int(x/scale))
   si=(sy*w+sx)*4;di=((y+(tile_h-nh)//2)*tile_w*6+col*tile_w+x+(tile_w-nw)//2)*4
   a=rgba[si+3]
   for k in range(3):pixels[di+k]=rgba[si+k]*a+pixels[di+k]*(1-a)
   pixels[di+3]=1.0
for i,(direction,name) in enumerate(views):
 p=root/name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==checks[direction]
 ref=bpy.data.images.load(str(p.resolve()),check_existing=False)
 render=bpy.data.images.load(str((out/(direction+"_face_detail.png")).resolve()),check_existing=False)
 blit(ref,i*2);blit(render,i*2+1)
 bpy.data.images.remove(ref);bpy.data.images.remove(render)
canvas.pixels[:]=pixels
canvas.filepath_raw=str((out/"MORWEN_REFERENCE_VROID_COMPARISON.png").resolve())
canvas.file_format="PNG";canvas.save()
(out/"COMPARISON_STATUS.json").write_text(json.dumps({"status":"REVIEW_ONLY","layout":["front_reference","front_render","right_reference","right_render","left_reference","left_render"],"reference_sha_verified":True,"landmark_alignment":"NOT_DONE","canonical_match":"NOT_APPROVED","geometry_modified":False},indent=2)+"\n")

# Second sheet: upper 42% of full-body reference, zoomed for head-focused review.
# This region is heuristic and deliberately NOT a measured face bounding box.
pixels=[0.14,0.14,0.16,1.0]*(tile_w*6*tile_h)
for i,(direction,name) in enumerate(views):
 ref=bpy.data.images.load(str((root/name).resolve()),check_existing=False)
 render=bpy.data.images.load(str((out/(direction+"_face_detail.png")).resolve()),check_existing=False)
 w,h=ref.size
 blit(ref,i*2,(0,int(h*.58),w,h))
 blit(render,i*2+1)
 bpy.data.images.remove(ref);bpy.data.images.remove(render)
canvas.pixels[:]=pixels
canvas.filepath_raw=str((out/"MORWEN_HEAD_FOCUSED_COMPARISON.png").resolve())
canvas.save()
(out/"HEAD_COMPARISON_STATUS.json").write_text(json.dumps({"status":"VISUAL_REVIEW_ONLY","reference_crop":"upper 42 percent, not anatomically registered","landmarks_aligned":False,"canonical_match":"NOT_APPROVED","source_geometry_modified":False},indent=2)+"\\n")
