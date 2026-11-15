"""Isolated architectural wall-section candidate: bonded limestone, lime mortar and timber.

2.1m x 1.8m wall with return at the right corner. No canonical changes.
"""
import bpy,random,math,json,os,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Vector
from aidan_dressed_stone_v2 import create_dressed_stone_v2
from aidan_material_variation_v1 import stone_material,timber_material
SEED=141127
rng=random.Random(SEED)
out=Path(os.environ.get("AIDAN_SECTION_OUTPUT","/tmp/aidan-wall-section"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
col=bpy.data.collections.new("ISOLATED_WALL_SECTION_CANDIDATE")
bpy.context.scene.collection.children.link(col)
def cube(name,loc,dim,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.name=name;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mat)
 return o
m=bpy.data.materials.new("warm lime mortar")
m.diffuse_color=(.53,.49,.40,1);m.use_nodes=True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.53,.49,.40,1)
m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.96
# Mortar face y=-0.20, nominal stone face y=-0.215: 15 mm recess.
# Previous backing face y=-0.065 left a 150 mm cavity and dark joints.
mortar_face=-.20
cube("continuous lime mortar backing",(0,-.08,.87),(2.1,.24,1.74),m)
cube("right-hand mortar return",(1.105,.20,.87),(.16,.50,1.74),m)
stones=[]
course_ends=[]
for row in range(6):
 z=.145+row*.285
 # Alternating coursing; each row tiles full wall width with variable blocks.
 # On odd courses, reserve a 170 mm front corner seat for a header quoin.
 # On even courses, front stones run to the outside corner (stretcher course).
 course_width=1.89 if row%2 else 2.06
 widths=[];remaining=course_width
 while remaining>.01:
  w=min(remaining,rng.uniform(.29,.54))
  if remaining-w<.17:w=remaining
  widths.append(w);remaining-=w
 x=-1.03
 for j,w in enumerate(widths):
  sid=len(stones)
  gap=.012
  center=(x+w/2,-.09,z+rng.uniform(-.006,.006))
  size=(w-gap,.25,.27+rng.uniform(-.008,.008))
  stone=create_dressed_stone_v2("bonded stone %03d"%sid,center,size,
       stone_material(sid,low_course=row<2,exposure=.45),col,
       seed=SEED+sid,cuts=5,chip=.07,relief=.035)
  stones.append(stone)
  x+=w
 course_ends.append(x)
# Alternating corner bond: odd rows expose a front-facing header that
# occupies the reserved seat; even rows use a narrow return-face stretcher.
quoins=[]
for row in range(6):
 sid=1000+row
 z=.145+row*.285
 if row%2:
  # Header projects into the front elevation and continues around the return.
  loc=(.995,-.005,z);dims=(.22,.43,.265)
 else:
  loc=(1.105,.165,z);dims=(.14,.31,.265)
 stone=create_dressed_stone_v2("corner return quoin %02d"%row,
    loc,dims,
    stone_material(sid,low_course=row<2),col,seed=SEED+sid,cuts=5)
 quoins.append(stone)
# Alternating corner headers and stretchers form a candidate corner bond.
# Physical contact and mesh-level intersections still require render review.
# Beam is physically seated across the wall, not floating above it.
wood=timber_material(3)
beam=cube("seated timber wall plate",(0,-.03,1.775),(2.19,.31,.19),wood)
# Nominal top of stone course 6: z=1.57+.135=1.705.
# Plate bottom 1.68, so there is 25 mm of seating, not a visible air gap.
assert beam.location.z-beam.dimensions.z/2 < .145+5*.285+.27/2
# End grain and two restrained wooden pegs.
pegmat=timber_material(4)
for i,x in enumerate((-.77,.76)):
 cube("timber peg %d"%i,(x,-.192,1.775),(.042,.015,.042),pegmat)
# Camera/light
world=bpy.context.scene.world or bpy.data.worlds.new("neutral study world")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
bpy.ops.object.light_add(type="AREA",location=(-3,-4,5))
bpy.context.object.data.energy=850;bpy.context.object.data.size=4
bpy.ops.object.camera_add(location=(3,-6,2.9))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=3.25
cam.rotation_euler=(Vector((0,.02,.9))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=1000;scene.render.resolution_y=800
scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
p=out/"wall_section.png";scene.render.filepath=str(p)
bpy.ops.render.render(write_still=True)
assert p.stat().st_size>1000
assert len(stones)>20 and len(quoins)==6
# Check nominal corner clearance and that every front-row stone stays
# inside its course envelope. These are AABB checks, not art approval.
for q in quoins:
 for o in stones:
  if abs(q.location.z-o.location.z)<.14:
   qxmin=q.location.x-q.dimensions.x/2
   omax=o.location.x+o.dimensions.x/2
   assert omax<=qxmin+.002,(o.name,q.name,omax,qxmin)
assert all(o.dimensions.x>0 and o.dimensions.z>0 for o in stones)
assert all(abs(end-(.86 if row%2 else 1.03))<.0001 for row,end in enumerate(course_ends))
assert all(quoins[row].location.x-quoins[row].dimensions.x/2>=course_ends[row]+.006 for row in range(6))
nominal_stone_face=-.09-.25/2
joint_recess=mortar_face-nominal_stone_face
assert .010<=joint_recess<=.020,("mortar joint depth",joint_recess)
assert abs((-.08-.24/2)-mortar_face)<1e-8
manifest={"status":"CANDIDATE_NOT_ART_APPROVED","stones":len(stones),
 "return_quoins":len(quoins),"mortar_backing":True,"timber_seated":True,
 "seed":SEED,"mortar_joint_recess_m":joint_recess,
 "corner_interlocking":"ALTERNATING_HEADER_STRETCHER_CANDIDATE", "blender":bpy.app.version_string,
 "image":"wall_section.png","sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
(out/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("AIDAN_SECTION_QA="+json.dumps(manifest))
