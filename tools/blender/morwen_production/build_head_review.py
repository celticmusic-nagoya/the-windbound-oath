"""Morwen head topology review mesh (NOT production approved).
Run: blender -b -t 2 --python tools/blender/morwen_production/build_head_review.py
Uses reproducible cross-section topology; hair and facial features deliberately excluded
until proportions are independently checked against canonical turnaround.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# Image Y-down 1024px -> Z-up, full-body review scale 4.8 Blender units.
S=4.8/987.0
def z(y): return (1003-y)*S
# Head: neck to upper cranium. Width/depth vary at each cross-section.
# Values are deliberately PROVISIONAL, not reference-derived anatomical measurements.
rings=[
 (241,.095,.080,0.000), (227,.117,.092,0.002),
 (207,.142,.115,-.010), (188,.165,.129,-.010),
 (166,.178,.141,-.012), (139,.180,.145,-.008),
 (110,.173,.142,-.004), (83,.153,.127,0.000),
 (65,.110,.100,0.005), (58,.045,.052,0.008),
]
N=32
verts=[]
for y,rx,ry,cy in rings:
 for i in range(N):
  a=2*math.pi*i/N
  # Jaw narrower in lower rings, soft cheek plane and slightly flattened front.
  x=rx*math.cos(a)
  depth=ry*math.sin(a)
  if depth<0: depth*=.91
  verts.append((x,cy+depth,z(y)))
faces=[]
for j in range(len(rings)-1):
 for i in range(N):
  a=j*N+i; bb=j*N+(i+1)%N
  faces.append((a,bb,bb+N,a+N))
faces.append(tuple(reversed(tuple(range(N)))))
faces.append(tuple((len(rings)-1)*N+i for i in range(N)))
mesh=bpy.data.meshes.new("MORWEN_HEAD_REVIEW_TOPOLOGY")
mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new("MORWEN_HEAD_REVIEW_NOT_APPROVED",mesh)
bpy.context.collection.objects.link(obj)
for p in mesh.polygons:p.use_smooth=True
sub=obj.modifiers.new("Surface smoothing review","SUBSURF");sub.levels=2;sub.render_levels=2
mat=bpy.data.materials.new("Warm neutral clay — geometry review")
mat.diffuse_color=(.56,.43,.36,1)
obj.data.materials.append(mat)
# Neutral lighting; no facial detail, hair, or hat means G2 cannot pass.
world=bpy.context.scene.world
world.color=(.22,.22,.22)
def camera(name,loc,look):
 bpy.ops.object.camera_add(location=loc)
 cam=bpy.context.object;cam.name=name
 cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.type='ORTHO';cam.data.ortho_scale=1.55
 return cam
center=(0,0,z(145))
cameras=[
 ("front",(0,-3,z(145))),
 ("right",(3,0,z(145))),
 ("back",(0,3,z(145))),
 ("left",(-3,0,z(145))),
 ("three_quarter",(2.5,-3.5,z(145)+1.4)),
]
bpy.ops.object.light_add(type='AREA',location=(1,-2,z(145)+2))
bpy.context.object.data.energy=450;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=3
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
out=Path("render_output/morwen_head_review");out.mkdir(parents=True,exist_ok=True)
for name,loc in cameras:
 scene.camera=camera("QA_CAMERA_"+name,loc,center)
 scene.render.filepath=str((out/(name+".png")).resolve())
 bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_HEAD_REVIEW_NOT_APPROVED.blend").resolve()))
(out/"QA.json").write_text(json.dumps({
 "status":"PROVISIONAL_TOPOLOGY_REVIEW","G1":"PARTIAL_UNAPPROVED_LANDMARKS",
 "G2":"NOT_RUN_FACE_HAIR_COSTUME_MISSING","G3":"RENDER_ATTEMPTED",
 "G4":"NOT_RUN","vertices":len(verts),"quads":(len(rings)-1)*N,
 "images":[name+".png" for name,_ in cameras]},indent=2)+"\n")
