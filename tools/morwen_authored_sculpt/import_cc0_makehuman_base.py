"""Read-only CC0 MakeHuman base mesh import and geometry QA. No character adoption.
Usage: blender -b --factory-startup --python-exit-code 1 --python this.py -- input.obj output_dir
"""
import bpy,sys,pathlib,hashlib,json,math
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:];src=pathlib.Path(argv[0]);out=pathlib.Path(argv[1]);out.mkdir(parents=True,exist_ok=True)
assert src.is_file() and src.stat().st_size>100000
sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(src),forward_axis="Y",up_axis="Z")
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert meshes,"OBJ_IMPORT_NO_MESH"
verts=sum(len(o.data.vertices) for o in meshes);faces=sum(len(o.data.polygons) for o in meshes)
assert verts>10000 and faces>10000,(verts,faces)
for ob in meshes:
 ob.name="CC0_MAKEHUMAN_UNMODIFIED_SOURCE_"+ob.name
 ob["source_url"]="https://github.com/makehumancommunity/mpfb2/blob/master/src/mpfb/data/3dobjs/base.obj"
 ob["source_sha256"]=sha
 ob.rotation_euler[0]=math.pi/2\n bpy.context.view_layer.objects.active=ob\n bpy.ops.object.select_all(action="DESELECT")\n ob.select_set(True)\n bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)\n ob["status"]="UNMODIFIED_SOURCE_ONLY_NOT_MORWEN"\n ob["orientation"]="SOURCE_Y_UP_TO_BLENDER_Z_UP_X_POS_90"\n clay=bpy.data.materials.new("CC0_SOURCE_NEUTRAL_CLAY")\n clay.diffuse_color=(0.65,0.59,0.53,1)\n clay.use_nodes=True\n clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.65,0.59,0.53,1)\n ob.data.materials.clear()\n ob.data.materials.append(clay)
scene=bpy.context.scene
scene["asset_status"]="CC0_SOURCE_IMPORT_NOT_CHARACTER_SCULPT"
scene["source_sha256"]=sha
scene["design_reference"]="MORWEN_LAYER0_NOT_YET_ALIGNED"
scene["license"]="CC0_BUNDLED_MAKEHUMAN_BASE_VERIFY_UPSTREAM"
# Neutral orthographic source-mesh views, not Morwen art renders.
from mathutils import Vector
worldpts=[ob.matrix_world @ v.co for ob in meshes for v in ob.data.vertices]
minv=Vector(tuple(min(v[i] for v in worldpts) for i in range(3)))
maxv=Vector(tuple(max(v[i] for v in worldpts) for i in range(3)))
center=(minv+maxv)/2
span=maxv-minv
assert min(span)>0.001,(minv,maxv)\nassert span.z>span.x and span.z>span.y,("UP_AXIS_INVALID",list(span))
camdata=bpy.data.cameras.new("CC0_SOURCE_ORTHO");cam=bpy.data.objects.new("CC0_SOURCE_ORTHO",camdata);scene.collection.objects.link(cam)
scene.camera=cam;camdata.type="ORTHO";camdata.ortho_scale=max(span.x,span.z)*1.22
ld=bpy.data.lights.new("CC0_SOURCE_LIGHT","AREA");lo=bpy.data.objects.new("CC0_SOURCE_LIGHT",ld);scene.collection.objects.link(lo)
lo.location=center+Vector((span.x*1.5,-span.y*2,span.z*1.5))
ld.energy=2500;ld.size=max(span)*1.5
lo.rotation_euler=(center-lo.location).to_track_quat("-Z","Y").to_euler()
scene.render.engine="CYCLES";scene.cycles.device="CPU";scene.cycles.samples=12
scene.render.resolution_x=480;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.film_transparent=True\nscene.view_settings.view_transform="Standard"
views={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}
for name,direction in views.items():
 cam.location=center+Vector(direction)*max(span)*2.5
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 scene.render.filepath=str(out/("source_"+name+".png"))
 bpy.ops.render.render(write_still=True)
 assert pathlib.Path(scene.render.filepath).stat().st_size>2000
blend=out/"MAKEHUMAN_CC0_UNMODIFIED_BASE_IMPORT_CANDIDATE.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
report={"status":"SOURCE_IMPORT_ONLY_NOT_SCULPT","source_sha256":sha,"source_size":src.stat().st_size,"blender":bpy.app.version_string,"meshes":len(meshes),"vertices":verts,"faces":faces,"blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest(),"source_bounds":{"min":list(minv),"max":list(maxv)},"source_views":list(views),"G1":"NOT_RUN_MORWEN_FIT","G2":"NOT_RUN","G3":"PARTIAL_IMPORT_ONLY","G4":"NOT_RUN"}
(out/"source_import_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("MAKEHUMAN_CC0_SOURCE_IMPORT",json.dumps(report))
