"""Non-destructive isolated clay comparison of scanned rock03 and rock06."""
import bpy,math,json,os,pathlib
from mathutils import Vector
out=pathlib.Path(os.environ.get("AIDAN_RENDER_OUT","/tmp/aidan-rock-review"));out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.world.color=(0.13,0.13,0.13)
for obj in list(bpy.data.objects):
    if obj.type not in {"MESH"}:
        bpy.data.objects.remove(obj,do_unlink=True)
for obj in bpy.data.objects:
    if obj.type=="MESH":obj.hide_render=True
mat=bpy.data.materials.new("QA_neutral_clay");mat.diffuse_color=(0.47,0.45,0.42,1)
mat.use_nodes=True
bsdf=mat.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(0.47,0.45,0.42,1)
bsdf.inputs["Roughness"].default_value=0.85
def track(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
camera_data=bpy.data.cameras.new("QA_camera");cam=bpy.data.objects.new("QA_camera",camera_data);scene.collection.objects.link(cam);scene.camera=cam
cam.data.type="ORTHO"
light_data=bpy.data.lights.new("QA_area","AREA");light=bpy.data.objects.new("QA_area",light_data);scene.collection.objects.link(light)
light_data.energy=850;light_data.shape="DISK";light_data.size=5
report={"status":"RENDERED_NOT_ART_APPROVED","blender":bpy.app.version_string,"items":[]}
for suffix in ("rock03","rock06"):
    matches=[o for o in bpy.data.objects if o.type=="MESH" and o.name.endswith(suffix)]
    assert len(matches)==1,(suffix,[o.name for o in matches])
    obj=matches[0]
    obj.hide_render=False
    old_materials=[m for m in obj.data.materials]
    obj.data.materials.clear();obj.data.materials.append(mat)
    bpy.context.view_layer.update()
    corners=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center=sum(corners,Vector())/len(corners)
    extent=max((max(p[i] for p in corners)-min(p[i] for p in corners)) for i in range(3))
    cam.data.ortho_scale=extent*1.85
    for view,offset in (("three_quarter",(1.6,-2.2,1.3)),("front",(0,-2.5,0.45)),("top",(0,-0.1,2.8))):
        cam.location=center+Vector(offset).normalized()*max(5,extent*3)
        track(cam,center)
        light.location=center+Vector((2,-3,5)).normalized()*max(4,extent*3)
        track(light,center)
        scene.render.filepath=str(out/f"{suffix}_{view}.png")
        bpy.ops.render.render(write_still=True)
    report["items"].append({"name":obj.name,"extent":round(extent,5),"renders":[f"{suffix}_{v}.png" for v in ("three_quarter","front","top")]})
    obj.data.materials.clear()
    for material in old_materials:
        obj.data.materials.append(material)
    obj.hide_render=True
(out/"render_audit.json").write_text(json.dumps(report,indent=2))
print("AIDAN_ROCK_RENDER="+json.dumps(report))
