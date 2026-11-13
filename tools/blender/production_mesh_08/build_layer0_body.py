"""Morwen Layer 0 anatomy mesh: deterministic geometric construction for art review.
Requires verified official PNGs; does not claim final canon or production art quality.
"""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/"layer0_reference_manifest.json").read_text())
for item in manifest["images"]:
    path=ROOT/"references"/item["filename"]
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=item["sha256"]:
        raise RuntimeError("Official reference missing/mismatched: "+item["view"])
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
parts=[]
def loft(name, rings, sides=24):
    verts=[];faces=[]
    for z,x,y,rx,ry in rings:
        for i in range(sides):
            t=2*math.pi*i/sides
            verts.append((x+rx*math.cos(t),y+ry*math.sin(t),z))
    for k in range(len(rings)-1):
        for i in range(sides):
            j=(i+1)%sides
            faces.append((k*sides+i,k*sides+j,(k+1)*sides+j,(k+1)*sides+i))
    faces.append(tuple(reversed(tuple(range(sides)))))
    faces.append(tuple((len(rings)-1)*sides+i for i in range(sides)))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for f in mesh.polygons:f.use_smooth=True
    parts.append(obj)
    return obj
# All dimensions are temporary modeling parameters, not official measurements.
loft("anatomy_torso",[
(.79,0,0,.135,.105),(.87,0,0,.165,.125),(.98,0,0,.145,.112),
(1.10,0,0,.124,.100),(1.20,0,0,.160,.115),(1.29,0,0,.200,.125),
(1.37,0,0,.178,.112),(1.43,0,0,.095,.083),(1.47,0,0,.062,.065)])
loft("anatomy_neck",[(1.39,0,0,.063,.062),(1.44,0,0,.061,.061),(1.49,0,0,.052,.054),(1.53,0,0,.060,.061)])
loft("anatomy_head",[
(1.48,0,-.010,.068,.077),(1.51,0,-.016,.095,.095),
(1.55,0,-.017,.114,.110),(1.61,0,0,.126,.115),
(1.67,0,.009,.121,.117),(1.72,0,.015,.106,.109),
(1.76,0,.014,.077,.088),(1.79,0,.010,.025,.036)])
for s,label in ((-1,"left"),(1,"right")):
    x=s*.106
    loft("anatomy_leg_"+label,[
        (.09,s*.108,-.004,.053,.066),(.17,s*.108,0,.054,.058),
        (.28,s*.111,0,.060,.064),(.40,s*.117,0,.063,.067),
        (.49,s*.118,0,.075,.077),(.58,s*.120,0,.080,.081),
        (.68,s*.118,0,.093,.093),(.78,s*.110,0,.100,.105),
        (.86,s*.096,0,.094,.097)])
    loft("anatomy_foot_"+label,[
        (.015,s*.108,-.066,.070,.128),(.055,s*.108,-.055,.073,.121),
        (.100,s*.108,-.022,.064,.080),(.135,s*.108,0,.052,.062)])
    # Downward relaxed arm, variable elbow and wrist cross sections.
    loft("anatomy_arm_"+label,[
        (.81,s*.263,-.004,.043,.048),(.89,s*.264,0,.045,.049),
        (1.00,s*.267,0,.047,.053),(1.09,s*.262,0,.053,.055),
        (1.18,s*.249,0,.061,.065),(1.28,s*.232,0,.073,.078),
        (1.36,s*.207,0,.077,.081)])
    loft("anatomy_hand_"+label,[
        (.72,s*.264,-.008,.026,.040),(.77,s*.264,-.006,.040,.044),
        (.82,s*.263,-.004,.042,.047),(.85,s*.263,0,.035,.040)])
# Fuse into one continuous surface, preserving organic contours for future retopology.
bpy.ops.object.select_all(action="DESELECT")
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
body=bpy.context.object;body.name="MORWEN_L0_ANATOMY_REVIEW_NOT_CANON"
remesh=body.modifiers.new("Continuous_surface_voxel","REMESH")
remesh.mode="VOXEL";remesh.voxel_size=.012
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=body.modifiers.new("Anatomical_relax","SMOOTH")
smooth.factor=1.1;smooth.iterations=6
bpy.ops.object.modifier_apply(modifier=smooth.name)
sub=body.modifiers.new("Surface_refinement","SUBSURF")
sub.levels=1;sub.render_levels=1
skin=bpy.data.materials.new("L0_neutral_clay_not_official");skin.diffuse_color=(.68,.52,.49,1)
body.data.materials.append(skin)
for poly in body.data.polygons:poly.use_smooth=True
for direction,xyz in {"front":(0,-4,1),"right":(-4,0,1),"back":(0,4,1),"left":(4,0,1)}.items():
    data=bpy.data.cameras.new(direction);obj=bpy.data.objects.new("CAM_"+direction,data);scene.collection.objects.link(obj)
    obj.location=xyz;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat("-Z","Y").to_euler()
    data.type="ORTHO";data.ortho_scale=2.12
engine_options={e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items}
scene.render.engine=next(e for e in ("BLENDER_EEVEE","BLENDER_EEVEE_NEXT","CYCLES") if e in engine_options)
scene.render.resolution_x=384;scene.render.resolution_y=576;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
for name,loc,power,size in [("KEY",(-2,-3,4),900,3),("FILL",(2,-1,2),500,2),("RIM",(0,3,3),700,3)]:
    light=bpy.data.lights.new(name,"AREA");light.energy=power;light.shape="DISK";light.size=size
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj)
    obj.location=loc;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat("-Z","Y").to_euler()
out=Path("render_output/layer0_anatomy");out.mkdir(parents=True,exist_ok=True)
for direction in ("front","right","back","left"):
    scene.camera=bpy.data.objects["CAM_"+direction]
    scene.render.filepath=str((out/(direction+".png")).resolve())
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_L0_ANATOMY_REVIEW.blend").resolve()))
report={"task":"MORWEN-L0-ANATOMY-01","blender":bpy.app.version_string,
"reference_sha256_verified":4,"render_count":len(list(out.glob("*.png"))),
"mesh_vertices":len(body.data.vertices),"mesh_faces":len(body.data.polygons),
"connected_mesh_object":True,"art_qa":"NOT_RUN","canonical_match":"NOT_VERIFIED",
"production_quality":False,"G1":"SOURCE_PASS_SHAPE_UNVERIFIED","G2":"NOT_RUN","G3":"RENDERED","G4":"NOT_RUN",
"warning":"Intermediate continuous anatomy mesh; not approved as final art."}
(out/"QA.json").write_text(json.dumps(report,indent=2)+"\n")
