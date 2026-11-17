"""Render five review views of the unapproved Morwen head/hair candidate.

python tools/character_blender/render_morwen_head_review.py -- INPUT.blend OUTPUT_DIR
No changes to input .blend or canonical sources. Artistic review is NOT_RUN.
"""
import bpy, math, json, hashlib, pathlib, sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2: raise SystemExit("usage: -- INPUT.blend OUTPUT_DIR")
src=pathlib.Path(args[0]).resolve();dest=pathlib.Path(args[1]).resolve()
if not src.is_file() or src.suffix!=".blend" or dest==src.parent: raise SystemExit("BLOCKED invalid paths")
before=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
if bpy.context.scene.get("asset_status")!="HEAD_HAIR_GEOMETRY_CANDIDATE_UNAPPROVED":
    raise SystemExit("BLOCKED incorrect source candidate")
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.render.image_settings.color_depth="8"
scene.view_settings.view_transform="Standard"
world=bpy.data.worlds.new("REVIEW_WORLD") if scene.world is None else scene.world
scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.65
def point(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add()
camera=bpy.context.object;camera.name="QA_CAMERA_NOT_ASSET"
camera.data.type="ORTHO";camera.data.ortho_scale=.39
scene.camera=camera
for name,loc,power,size in [
    ("KEY",(.4,-.5,.6),250,1.1),("FILL",(-.5,-.2,.4),160,1.3),("RIM",(.1,.5,.55),280,.9)]:
    bpy.ops.object.light_add(type="AREA",location=loc)
    ob=bpy.context.object;ob.name="QA_LIGHT_"+name
    ob.data.energy=power;ob.data.shape="DISK";ob.data.size=size
    point(ob,(0,0,.14))
dest.mkdir(parents=True,exist_ok=True)
views={"front":(0,-1,0),"back":(0,1,0),"facing_right":(1,0,0),
       "facing_left":(-1,0,0),"three_quarter":(.7,-.7,.1)}
outputs={}
for name,axis in views.items():
    direction=Vector(axis).normalized()
    camera.location=Vector((0,0,.145))+direction*.85
    point(camera,(0,0,.145))
    path=dest/("MORWEN_HEAD_"+name.upper()+".png")
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    if not path.is_file() or path.stat().st_size<1000:
        raise SystemExit("BLOCKED render missing "+name)
    outputs[name]={"file":path.name,"bytes":path.stat().st_size,
                   "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
after=hashlib.sha256(src.read_bytes()).hexdigest()
if before!=after:raise SystemExit("BLOCKED source blend changed")
report={"status":"PASS_FIVE_REVIEW_RENDERS_ONLY","input_blend_sha256":before,
        "source_unchanged":True,"renders":outputs,"G1":"BLOCKED",
        "G2":"NOT_RUN","G3":"RENDER_FILES_ONLY","G4":"NOT_RUN",
        "production_approval":False}
(dest/"MORWEN_HEAD_REVIEW_REPORT.json").write_text(json.dumps(report,indent=2))
print(json.dumps({"status":report["status"],"views":list(outputs)}))
