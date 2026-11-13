"""MAP-BLENDER-08: isolated, provisional Rilde geography blockout. Blender 3.x+."""
import bpy, math, os, json, hashlib
from mathutils import Vector
from pathlib import Path
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(0.16,0.21,0.27)
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
grass=material("Grass",(0.25,0.39,0.22))
water=material("Water",(0.12,0.31,0.45))
stone=material("Stone",(0.43,0.42,0.38))
roof=material("Roof",(0.52,0.19,0.12))
wood=material("Timber",(0.39,0.27,0.17))
sand=material("Path",(0.58,0.48,0.32))
def cube(name,xyz,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
 o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mat)
 return o
cube("Village terrain",(0,0,-0.3),(38,34,0.6),grass)
cube("Eastern river",(16,0,0.02),(5,40,0.08),water)
cube("Eastern bridge",(16,2,0.3),(7,2.5,0.45),wood)
cube("Northern road",(0,12,0.02),(3,13,0.07),sand)
cube("Village square",(0,0,0.02),(9,8,0.06),stone)
for i,(x,y) in enumerate([(-8,4),(-4,7),(6,6),(9,1),(-7,-5),(4,-7)]):
 cube("House %02d"%i,(x,y,1.3),(3.2,3.1,2.6),wood)
 cube("Roof %02d"%i,(x,y,2.85),(3.9,3.8,0.55),roof)
cube("Western cliff plateau",(-23,10,2.5),(11,17,5),stone)
cube("Ocean west",(-36,0,-0.45),(17,65,0.1),water)
cube("Intervening ridge",(-13,8,3.3),(4,18,6.6),stone)
cube("Southwest fishing inlet",(-26,-19,-0.25),(12,9,0.12),water)
cube("Southeast forest marker",(24,-20,1.0),(10,10,2),grass)
cube("Return road bend marker",(-12,0,0.05),(3,7,0.1),sand)
def camera(name,location,target):
 bpy.ops.object.camera_add(location=location)
 c=bpy.context.object;c.name=name
 direction=Vector(target)-c.location
 c.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
 c.data.type='ORTHO';c.data.ortho_scale=49
 return c
camera("FIELD_27_DEG_PROVISIONAL",(35,-47,31),(0,0,0))
camera("CLIFF_CG_PROVISIONAL",(-31,18,11),(-38,5,0))
camera("RETURN_BEND_PROVISIONAL",(-14,-10,9),(0,0,0))
bpy.ops.object.light_add(type='SUN',location=(0,0,20))
bpy.context.object.data.energy=2
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_blockout.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_blockout.blend"))
files=["rilde_blockout.png","rilde_blockout.blend"]
report={"task":"MAP-BLENDER-08","status":"BLOCKOUT_ONLY","canon_coordinates":"PROVISIONAL","cg_visual_match":"NOT_VERIFIED","cliff_occlusion":"NOT_VERIFIED","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files}}
(out/"build_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
