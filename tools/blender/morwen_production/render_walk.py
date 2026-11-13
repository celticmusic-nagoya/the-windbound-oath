"""32-frame review renderer. Never renders without a verified approved master."""
import bpy,math,json,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
runpy.run_path(str(ROOT/"preflight.py"),run_name="__main__")
scene=bpy.context.scene;rig=bpy.data.objects["MORWEN_MASTER_RIG"]
scene.frame_start=1;scene.frame_end=8
scene.render.resolution_x=384;scene.render.resolution_y=576;scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
engines={e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items}
scene.render.engine=next(e for e in ("BLENDER_EEVEE","BLENDER_EEVEE_NEXT","CYCLES") if e in engines)
# Character front = -Y, character RIGHT = +X; front camera sees +X at SCREEN LEFT.
views={"front":(0,-4,1),"right":(4,0,1),"back":(0,4,1),"left":(-4,0,1)}
for direction,loc in views.items():
    cam_data=bpy.data.cameras.new(direction)
    cam=bpy.data.objects.new("MORWEN_CAM_"+direction,cam_data)
    scene.collection.objects.link(cam);cam.location=loc
    cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat("-Z","Y").to_euler()
    cam_data.type="ORTHO";cam_data.ortho_scale=2.2
def rotate(name,axis,value):
    bone=rig.pose.bones.get(name)
    if bone:
        bone.rotation_mode="XYZ";bone.rotation_euler[axis]=value
for frame in range(1,9):
    scene.frame_set(frame);phase=2*math.pi*(frame-1)/8
    for side in ("L","R"):
        stride=math.sin(phase+(0 if side=="L" else math.pi))
        rotate("thigh."+side,0,.26*stride)
        rotate("shin."+side,0,.10+.18*max(0,-stride))
        rotate("foot."+side,0,-.10*stride)
        rotate("upper_arm."+side,0,-.18*stride)
        rotate("forearm."+side,0,-.08)
    rotate("spine_01",2,.025*math.sin(2*phase))
    rotate("pelvis",2,.035*math.sin(phase))
    for bone in rig.pose.bones:
        if bone.rotation_mode=="XYZ":bone.keyframe_insert(data_path="rotation_euler",frame=frame)
out=Path("render_output/morwen_walk");out.mkdir(parents=True,exist_ok=True)
for direction in views:
    scene.camera=bpy.data.objects["MORWEN_CAM_"+direction]
    for frame in range(1,9):
        scene.frame_set(frame)
        scene.render.filepath=str((out/f"{direction}_{frame:02d}.png").resolve())
        bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_WALK_REVIEW.blend").resolve()))
(out/"render_metadata.json").write_text(json.dumps({"frames":32,"garter":"RIGHT +X, front screen LEFT, back screen RIGHT","production_approved":False},indent=2))
