"""Side-by-side diagnostic of verified macro support and original scan patch.
Never imply physically registered world-space placement or production quality.
"""
import argparse, bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--scan-blend",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
 out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 scan=Path(a.scan_blend).resolve()
 assert scan.exists() and scan.stat().st_size>1000000
 macro=bpy.data.objects.get("LIND_MACRO_CLIFF_OBJ_DIAGNOSTIC_NOT_CANON")
 assert macro and len(macro.data.polygons)>1000
 with bpy.data.libraries.load(str(scan),link=False) as (source,target):
  assert "LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY" in source.objects
  target.objects=["LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY"]
 patch=target.objects[0]
 assert patch and patch.type=="MESH"
 bpy.context.scene.collection.objects.link(patch)
 patch.name="SCAN_PATCH_REFERENCE_NOT_ALIGNED"
 # Side-by-side size normalization for *visual comparison only*.
 # The publisher scan is not metrically registered to the macro support.
 points=[Vector(c) for c in patch.bound_box]
 mins=[min(p[i] for p in points) for i in range(3)]
 maxs=[max(p[i] for p in points) for i in range(3)]
 span=max(maxs[i]-mins[i] for i in range(3))
 assert span>0
 scale=1.8/span
 patch.scale=(scale,)*3
 center=Vector([(mins[i]+maxs[i])/2 for i in range(3)])
 patch.location=Vector((2.6,0,.5))-center*scale
 patch.display_type="TEXTURED"
 scene=bpy.context.scene
 camd=bpy.data.cameras.new("REFERENCE_COMPARISON_CAMERA")
 cam=bpy.data.objects.new("REFERENCE_COMPARISON_CAMERA",camd)
 scene.collection.objects.link(cam)
 cam.location=(4,-9,5)
 aim=Vector((1.25,.5,.45))
 cam.rotation_euler=(aim-cam.location).to_track_quat("-Z","Y").to_euler()
 camd.type="ORTHO";camd.ortho_scale=7.4
 scene.camera=cam
 scene.render.engine="BLENDER_WORKBENCH"
 scene.display.shading.light="STUDIO"
 scene.display.shading.color_type="OBJECT"
 scene.display.shading.show_cavity=True
 macro.color=(.63,.68,.72,1)
 patch.color=(.71,.57,.39,1)
 scene.render.resolution_x=1400;scene.render.resolution_y=800
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 png=out/"macro_vs_scan_side_by_side.png"
 scene.render.filepath=str(png)
 print("REFERENCE_RENDER_START",flush=True)
 bpy.ops.render.render(write_still=True)
 print("REFERENCE_RENDER_DONE",flush=True)
 assert png.exists() and png.stat().st_size>10000
 metrics={"production_ready":False,"world_alignment":"NOT_DEFINED","collision":"MACRO_ONLY_UNAPPROVED","source_scan_role":"REFERENCE_ONLY","scan_faces":len(patch.data.polygons),"macro_faces":len(macro.data.polygons),"render_sha256":hashlib.sha256(png.read_bytes()).hexdigest(),"scan_blend_sha256":hashlib.sha256(scan.read_bytes()).hexdigest(),"G1":"BLOCKED","G2":"NOT_RUN","G3":"REFERENCE_SCENE_ONLY","G4":"NOT_RUN"}
 (out/"comparison_manifest.json").write_text(json.dumps(metrics,indent=2)+"\n")
 print("REFERENCE_COMPARISON_COMPLETE",flush=True)
if __name__=="__main__":main()
