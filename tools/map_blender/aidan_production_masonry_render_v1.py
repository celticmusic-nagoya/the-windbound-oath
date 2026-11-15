"""Headless diagnostic renderer for the isolated Aidan masonry candidate."""
import bpy, os, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_production_masonry_v1 import build_masonry, MasonrySpec

out=Path(os.environ.get("AIDAN_MASONRY_OUTPUT","/tmp/aidan-masonry-qa"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
spec=MasonrySpec()
report=build_masonry(spec)
assert report["stone_count"]>250, report
stones=[o for o in bpy.data.objects if o.name.endswith("ashlar") or " ashlar " in o.name]
assert len(stones)==report["stone_count"], (len(stones),report)
assert all(o.type=="MESH" and len(o.data.polygons)==6 for o in stones)
# Verify that no stone penetrates the central door opening or right-side window.
door_violations=[];window_violations=[]
for o in stones:
 x,y,z=o.location
 sx,sy,sz=o.dimensions
 if o.name.startswith("south") and abs(x)<.785 and z-sz/2<2.20:
  if x+sx/2>-.785 and x-sx/2<.785:door_violations.append(o.name)
 if o.name.startswith("east") and z+sz/2>1.12 and z-sz/2<2.47:
  if y+sy/2>-.495 and y-sy/2<1.395:window_violations.append(o.name)
assert not door_violations, "Door intrusion: "+str(door_violations[:5])
assert not window_violations, "Window intrusion: "+str(window_violations[:5])
# Opening boundary stones must be within a mortar gap of exact architectural heights.
def edge_error(side, horizontal_test, target_z, above):
 candidates=[]
 for o in stones:
  if not o.name.startswith(side): continue
  x,y,z=o.location; sx,sy,sz=o.dimensions
  if not horizontal_test(x,y,sx,sy):continue
  edge=z-sz/2 if above else z+sz/2
  if (above and edge>=target_z-0.001) or (not above and edge<=target_z+0.001):
   candidates.append(abs(edge-target_z))
 assert candidates, "Missing boundary stones: "+side+str(target_z)
 err=min(candidates)
 assert err<=spec.mortar_gap+0.002, (side,target_z,err)
 return round(err,5)
window_band=lambda x,y,sx,sy: .0<y<.85
south_band=lambda x,y,sx,sy: .0<x<1.2
boundary_errors={
 "door_top":edge_error("south",south_band,2.20,True),
 "window_bottom":edge_error("east",window_band,1.12,False),
 "window_top":edge_error("east",window_band,2.47,True),
}
report["qa"]={"stone_mesh_count":len(stones),"door_intrusions":0,"window_intrusions":0,"opening_boundary_error_m":boundary_errors}
world=bpy.context.scene.world or bpy.data.worlds.new("masonry world")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.7,.72,.76,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
bpy.ops.object.light_add(type="AREA",location=(-6,-8,11))
bpy.context.object.data.energy=1800
bpy.context.object.data.size=8
bpy.ops.object.camera_add()
cam=bpy.context.object
cam.data.type="ORTHO";cam.data.ortho_scale=13
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="CYCLES";scene.cycles.samples=12
scene.cycles.use_denoising=False
for layer in scene.view_layers:
 if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
scene.render.resolution_x=640;scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
target=Vector((0,0,1.6))
views={"front":(0,-14,7),"right":(14,0,7),"game27":(10,-10,1.6+math.tan(math.radians(27))*math.sqrt(200))}
report["views"]=[]
for name,pos in views.items():
 cam.location=pos
 cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
 p=out/("aidan_masonry_"+name+".png")
 scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 report["views"].append({"name":name,"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
bpy.ops.wm.save_as_mainfile(filepath=str(out/"aidan_masonry_candidate.blend"))
(out/"manifest.json").write_text(json.dumps(report,indent=2))
print("AIDAN_MASONRY_RENDER="+json.dumps(report))
