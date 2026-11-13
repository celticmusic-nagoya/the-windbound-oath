"""Noncanonical layered diagnostic render. Does NOT claim official-art fidelity."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
layers={k:[] for k in ["L0_BODY","L1_INNER","L2_UNIFORM","L3_ACCESSORIES"]}
def material(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
skin=material("skin",(.75,.52,.49));purple=material("purple",(.21,.09,.34));dark=material("dark",(.055,.04,.09));gold=material("gold",(.75,.55,.23))
def shape(name,layer,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc)
 ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(mat);layers[layer].append(ob)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
shape("torso","L0_BODY",(0,0,1.06),(.17,.10,.32),skin)
shape("head","L0_BODY",(0,0,1.52),(.115,.10,.145),skin)
for x,side in ((.1,"right"),(-.1,"left")):
 shape("leg_"+side,"L0_BODY",(x,0,.45),(.07,.07,.39),skin)
 shape("arm_"+side,"L0_BODY",(x*2.4,0,1.1),(.055,.055,.27),skin)
 shape("sock_"+side,"L1_INNER",(x,0,.27),(.073,.073,.20),dark)
 shape("boot_"+side,"L2_UNIFORM",(x,-.025,.09),(.08,.12,.085),dark)
 shape("sleeve_"+side,"L2_UNIFORM",(x*2.4,0,1.1),(.07,.07,.27),purple)
shape("bodice","L2_UNIFORM",(0,0,1.08),(.18,.12,.27),purple)
shape("skirt","L2_UNIFORM",(0,0,.79),(.25,.20,.16),dark)
shape("cape","L3_ACCESSORIES",(0,.10,1.03),(.26,.11,.36),purple)
shape("hat_brim","L3_ACCESSORIES",(0,0,1.68),(.28,.24,.025),purple)
shape("hat_crown","L3_ACCESSORIES",(0,0,1.79),(.16,.14,.15),purple)
shape("right_leg_garter_only","L3_ACCESSORIES",(.10,0,.48),(.077,.077,.022),gold)
shape("satchel","L3_ACCESSORIES",(-.23,.08,.95),(.10,.07,.13),dark)
for name,xyz in {"front":(0,-4,1),"right":(-4,0,1),"back":(0,4,1),"left":(4,0,1)}.items():
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new("CAM_"+name,d);bpy.context.collection.objects.link(o);o.location=xyz
 o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat("-Z","Y").to_euler();d.type="ORTHO";d.ortho_scale=2.25
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=384;scene.render.resolution_y=576;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
world=scene.world;world.color=(.7,.7,.7)
out=Path("render_output");out.mkdir(exist_ok=True)
for stage,visible in enumerate((1,2,3,4)):
 for i,objects in enumerate(layers.values()):
  for ob in objects:ob.hide_render=i>=visible
 for direction in ("front","right","back","left"):
  scene.camera=bpy.data.objects["CAM_"+direction];scene.render.filepath=str((out/f"L{stage}_{direction}.png").resolve());bpy.ops.render.render(write_still=True)
for objects in layers.values():
 for ob in objects:ob.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_DIAGNOSTIC.blend").resolve()))
files=list(out.glob("L[0-3]_*.png"))
report={"rendered_frames":len(files),"render_success":len(files)==16,"official_reference_images_in_job":False,"art_qa":"NOT_RUN","production_quality":False,"garter":"character right +X; front screen right; back screen left","model":"PRIMITIVE DIAGNOSTIC ONLY"}
(out/"QA.json").write_text(json.dumps(report,indent=2)+"\n")
if len(files)!=16:raise RuntimeError("Missing render frames")
