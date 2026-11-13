"""Inspect pinned MPFB base mesh in Blender; source CC0 license audit separately.
Not a Morwen production model. No sculpt or official design claim.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path("_upstream_mpfb")
source=root/"src/mpfb/data/3dobjs/base.obj"
assert source.is_file(),source
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
if hasattr(bpy.ops.wm,"obj_import"):bpy.ops.wm.obj_import(filepath=str(source.resolve()))
else:bpy.ops.import_scene.obj(filepath=str(source.resolve()))
meshes=[o for o in bpy.context.selected_objects if o.type=="MESH"]
assert meshes,"No mesh imported"
obj=max(meshes,key=lambda x:len(x.data.vertices))
obj.name="MPFB_CC0_BASE_INSPECTION_NOT_MORWEN"
bpy.context.view_layer.update()
# Analyze source coordinate bounds and use top 30% of the model for head inspection.
coords=[obj.matrix_world@v.co for v in obj.data.vertices]
mins=[min(p[i] for p in coords) for i in range(3)]
maxs=[max(p[i] for p in coords) for i in range(3)]
spans=[b-a for a,b in zip(mins,maxs)]
axis=max(range(3),key=lambda i:spans[i])
head_axis=maxs[axis]-.115*spans[axis]
center=Vector([(mins[i]+maxs[i])/2 for i in range(3)])
center[axis]=head_axis
# Rotate imported mesh into Z-up if necessary, using dominant height axis.
if axis==1:
 obj.rotation_euler[0]=math.pi/2
 bpy.context.view_layer.update()
 coords=[obj.matrix_world@v.co for v in obj.data.vertices]
 mins=[min(p[i] for p in coords) for i in range(3)]
 maxs=[max(p[i] for p in coords) for i in range(3)]
 spans=[b-a for a,b in zip(mins,maxs)]
center=Vector([(mins[i]+maxs[i])/2 for i in range(3)])
center.z=maxs[2]-.12*spans[2]
scale=max(spans[0],spans[1],spans[2]*.25)
mat=bpy.data.materials.new("Neutral clay inspection")
mat.diffuse_color=(.61,.48,.40,1)
obj.data.materials.clear();obj.data.materials.append(mat)
bpy.ops.object.light_add(type="AREA",location=(center.x+scale,center.y-scale,center.z+scale))
bpy.context.object.data.energy=700;bpy.context.object.data.size=scale*2
world=bpy.context.scene.world;world.color=(.32,.32,.32)
scene=bpy.context.scene;scene.render.engine="CYCLES";scene.cycles.samples=20
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
out=Path("render_output/morwen_mpfb_base_review");out.mkdir(parents=True,exist_ok=True)
for name,dx,dy,dz in [("front",0,-1,0),("right",1,0,0),("back",0,1,0),("left",-1,0,0),("three_quarter",.7,-1,.45)]:
 bpy.ops.object.camera_add(location=center+Vector((dx,dy,dz))*scale*3)
 cam=bpy.context.object;cam.name="INSPECTION_CAMERA_"+name
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=scale*1.7
 scene.camera=cam;scene.render.filepath=str((out/(name+".png")).resolve())
 bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MPFB_BASE_INSPECTION_NOT_MORWEN.blend").resolve()))
(out/"QA.json").write_text(json.dumps({"schema":"MORWEN-MPFB-BASE-REVIEW-01","source":str(source),"vertices":len(obj.data.vertices),"faces":len(obj.data.polygons),"bounds":dict(min=mins,max=maxs),"G1":"NOT_RUN_BASE_NOT_MORWEN","G2":"NOT_RUN_BASE_NOT_SCULPTED","G3":"RENDERED","G4":"NOT_RUN","production_approved":False},indent=2)+"\n")
