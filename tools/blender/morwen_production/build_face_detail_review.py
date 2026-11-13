"""Morwen face detail placement review. NOT official art or production-approved.
Runs head topology generator, adds separated anatomical review components,
then re-renders all five angles. No canonical files are modified.
"""
import bpy, math, json, runpy
from pathlib import Path
from mathutils import Vector
runpy.run_path(str(Path(__file__).with_name("build_head_review.py")),run_name="__main__")
scene=bpy.context.scene
S=4.8/987.0
def z(y):return (1003-y)*S
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
 m.use_nodes=True
 bs=m.node_tree.nodes.get("Principled BSDF")
 bs.inputs["Base Color"].default_value=(*color,1)
 bs.inputs["Metallic"].default_value=metal
 return m
skin=mat("Warm skin",(0.72,.52,.46))
purple=mat("Purple hair",(0.17,.065,.24))
iris=mat("Violet iris",(0.28,.13,.42))
white=mat("Sclera",(0.91,.83,.81))
gold=mat("Glasses warm gold",(.68,.43,.13),.7)
def uv(name,loc,scale,material,segments=32,rings=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def curve(name,points,bevel,material,cyclic=False):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=bevel;cu.bevel_resolution=3
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 sp.use_cyclic_u=cyclic
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 return o
# Coordinates correspond to head review's provisional dimensions. Front is -Y.
# Eye spacing and feature geometry remain visual review candidates.
for side,letter in [(-1,"L"),(1,"R")]:
 x=side*.083
 uv("eye_sclera_"+letter,(x,-.127,z(146)),(.052,.020,.030),white)
 uv("iris_"+letter,(x,-.146,z(146)),(.021,.008,.023),iris)
 # Eyelids use two arched contours rather than texture-only facial details.
 for upper in [True,False]:
  points=[]
  for i in range(13):
   t=math.pi*i/12
   px=x-.054+(.108*i/12)
   py=-.128-.004*math.sin(t)
   pz=z(146)+(.031 if upper else -.030)*math.sin(t)
   points.append((px,py,pz))
  curve(("upper_" if upper else "lower_")+"eyelid_"+letter,points,.006,skin)
 # Sculpt-like ear review geometry with nested helix curve.
 ex=side*.178
 uv("ear_"+letter,(ex,-.002,z(155)),(.029,.032,.064),skin)
 pts=[(ex+side*(.015+.009*math.sin(t)), -.034+.007*math.cos(t),z(155)+.048*math.cos(t)) for t in [2*math.pi*i/28 for i in range(28)]]
 curve("ear_helix_"+letter,pts,.005,skin,True)
# Nose bridge and tip are distinct provisional sculpt components, not finished topology.
uv("nose_bridge",(0,-.144,z(172)),(.021,.026,.062),skin)
uv("nose_tip",(0,-.168,z(193)),(.031,.031,.022),skin)
for side,letter in [(-1,"L"),(1,"R")]:
 uv("nose_ala_"+letter,(side*.026,-.154,z(195)),(.018,.018,.014),skin)
uv("mouth_upper_lip",(0,-.124,z(215)),(.055,.012,.009),skin)
uv("mouth_lower_lip",(0,-.123,z(219)),(.051,.012,.011),skin)
# Hair is layered directional locks; not a helmet or a single solid primitive.
for i in range(15):
 a=2*math.pi*i/15
 x=.14*math.cos(a); y=.11*math.sin(a)
 # Back and side bob, with crown starting high and tips at jaw.
 points=[(x*.55,y*.55,z(68)),(x*.96,y*.98,z(93)),
         (x*1.10,y*1.09,z(145)),(x*1.02,y*1.13,z(205))]
 curve("bob_lock_%02d"%i,points,.024,purple)
for i in range(7):
 x=(i-3)*.040
 points=[(x*.7,-.10,z(68)),(x,-.148,z(93)),(x*1.1,-.151,z(117+i%3*6))]
 curve("fringe_%02d"%i,points,.021,purple)
# Thin round glasses with bridge and temple curves.
for side,letter in [(-1,"L"),(1,"R")]:
 x=side*.083
 points=[(x+.062*math.cos(2*math.pi*i/64),-.163,z(146)+.047*math.sin(2*math.pi*i/64)) for i in range(64)]
 curve("round_glasses_"+letter,points,.004,gold,True)
 curve("glasses_temple_"+letter,[(x+side*.062,-.159,z(146)),(side*.18,-.055,z(150))],.004,gold)
curve("glasses_bridge",[(-.021,-.164,z(146)),(0,-.17,z(150)),(.021,-.164,z(146))],.004,gold)
out=Path("render_output/morwen_face_detail_review");out.mkdir(parents=True,exist_ok=True)
for name in ["front","right","back","left","three_quarter"]:
 scene.camera=bpy.data.objects["QA_CAMERA_"+name]
 scene.render.filepath=str((out/(name+".png")).resolve())
 bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_FACE_DETAIL_REVIEW_NOT_APPROVED.blend").resolve()))
(out/"QA.json").write_text(json.dumps({
 "status":"DETAIL_PLACEMENT_REVIEW_NOT_APPROVED",
 "G1":"PROVISIONAL_NOT_APPROVED",
 "G2":"NOT_PASSED_SEPARATE_PRIMITIVES_NOT_INTEGRATED_TOPOLOGY",
 "G3":"FIVE_RENDERS_CREATED",
 "G4":"NOT_RUN",
 "notes":"Facial details and locks are separate review objects; require continuous facial retopology and canonical art comparison."
},indent=2)+"\n")
