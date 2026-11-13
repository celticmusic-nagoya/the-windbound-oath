"""Render isolated geometry QA preview, not production artwork."""
import bpy, math, os, json, hashlib
from mathutils import Vector
from aidan_roof_candidate_01 import build
out=os.environ.get("AIDAN_ROOF_OUTPUT","/tmp/aidan-roof-qa")
os.makedirs(out,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
result=build()
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT"
scene.render.resolution_x=1000
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=True
scene.world.color=(.23,.23,.23)
def camera(name,azimuth):
    data=bpy.data.cameras.new(name)
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    target=Vector((0,0,4.3))
    elev=math.radians(27)
    dist=16
    obj.location=(dist*math.cos(azimuth)*math.cos(elev),dist*math.sin(azimuth)*math.cos(elev),target.z+dist*math.sin(elev))
    direction=target-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    data.type="ORTHO"
    data.ortho_scale=12.8
    scene.camera=obj
    return obj
light_data=bpy.data.lights.new("QA_Key","AREA")
light=bpy.data.objects.new("QA_Key",light_data)
scene.collection.objects.link(light)
light.location=(2,-5,11)
light_data.energy=1300
light_data.shape="DISK"
light_data.size=8
manifest={"status":"GEOMETRY_ONLY_NO_PBR_NO_ART_APPROVAL","roof":result,"views":[]}
for name,az in [("game_27deg",math.radians(-55)),("front",math.radians(-90)),("rear",math.radians(90)),("left",math.pi),("right",0)]:
    camera(name,az)
    path=os.path.join(out,name+".png")
    scene.render.filepath=path
    bpy.ops.render.render(write_still=True)
    with open(path,"rb") as f: sha=hashlib.sha256(f.read()).hexdigest()
    manifest["views"].append({"name":name,"file":os.path.basename(path),"sha256":sha,"bytes":os.path.getsize(path)})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"aidan_roof_geometry_candidate.blend"))
with open(os.path.join(out,"manifest.json"),"w") as f:json.dump(manifest,f,indent=2)
print("AIDAN_ROOF_QA="+json.dumps(manifest))
