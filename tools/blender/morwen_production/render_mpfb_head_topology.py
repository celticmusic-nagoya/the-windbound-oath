"""Head-focused MPFB source inspection, no official Morwen asset modifications."""
import bpy,json
from pathlib import Path
from mathutils import Vector
src=Path("render_output/morwen_mpfb_base_review/MPFB_BASE_INSPECTION_NOT_MORWEN.blend")
assert src.exists()
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
obj=bpy.data.objects["MPFB_CC0_BASE_INSPECTION_NOT_MORWEN"]
coords=[obj.matrix_world@v.co for v in obj.data.vertices]
zmin=min(v.z for v in coords);zmax=max(v.z for v in coords)
height=zmax-zmin
center=Vector((sum((min(v.x for v in coords),max(v.x for v in coords)))/2,
               sum((min(v.y for v in coords),max(v.y for v in coords)))/2,
               zmax-.105*height))
out=Path("render_output/morwen_mpfb_head_topology");out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.cycles.samples=28
for name in ["front","right","back","left","three_quarter"]:
 cam=bpy.data.objects["INSPECTION_CAMERA_"+name]
 direction=(cam.location-center).normalized()
 cam.location=center+direction*height
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.ortho_scale=height*.43
 scene.camera=cam
 scene.render.filepath=str((out/(name+"_head.png")).resolve())
 bpy.ops.render.render(write_still=True)
# Topology overlay, wireframe edges visible over clay
wire=bpy.data.materials.new("Topology dark lines")
wire.diffuse_color=(.025,.025,.025,1)
wire.use_nodes=True
bsdf=wire.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value=(.012,.012,.012,1)
duplicate=obj.copy();duplicate.data=obj.data.copy()
bpy.context.collection.objects.link(duplicate)
duplicate.name="TOPOLOGY_EDGES_INSPECTION"
duplicate.data.materials.clear();duplicate.data.materials.append(wire)
mod=duplicate.modifiers.new("Topology edges","WIREFRAME")
mod.thickness=height*.00035
mod.use_replace=True
for name in ["front","right","three_quarter"]:
 scene.camera=bpy.data.objects["INSPECTION_CAMERA_"+name]
 scene.render.filepath=str((out/(name+"_wire.png")).resolve())
 bpy.ops.render.render(write_still=True)
report={"source":"MPFB v2.0.18 base.obj","vertices":len(obj.data.vertices),
 "faces":len(obj.data.polygons),"head_crop":"top 43% of full height",
 "head_region_vertices":sum(1 for v in coords if v.z>zmax-height*.25),
 "G1":"NOT_APPROVED_NOT_MORWEN","G2":"REQUIRES_VISUAL_REVIEW",
 "G3":"RENDER_AND_WIREFRAME_INSPECTION","G4":"NOT_RUN",
 "production_approved":False}
(out/"QA.json").write_text(json.dumps(report,indent=2)+"\n")
