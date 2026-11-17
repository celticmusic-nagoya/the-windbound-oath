"""Render an already saved .blend without rebuilding geometry. Technical clay QA only."""
import argparse, bpy, json, hashlib, sys, math
from pathlib import Path
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    obj=bpy.data.objects.get("LIND_MACRO_CLIFF_OBJ_DIAGNOSTIC_NOT_CANON")
    assert obj and obj.type=="MESH" and len(obj.data.polygons)>1000
    scene=bpy.context.scene
    camera_data=bpy.data.cameras.new("QA_ORTHOGRAPHIC_CAMERA")
    cam=bpy.data.objects.new("QA_ORTHOGRAPHIC_CAMERA",camera_data)
    scene.collection.objects.link(cam)
    cam.location=(5,-7,4)
    target=Vector((0,.6,.45))
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    camera_data.type="ORTHO"
    camera_data.ortho_scale=4.7
    scene.camera=cam
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_cavity=True
    scene.render.resolution_x=1200
    scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str((out/"lind_macro_technical_clay.png").resolve())
    print("WORKBENCH_RENDER_START",flush=True)
    bpy.ops.render.render(write_still=True)
    print("WORKBENCH_RENDER_DONE",flush=True)
    png=out/"lind_macro_technical_clay.png"
    assert png.exists() and png.stat().st_size>10000
    metrics={"production_ready":False,"technical_only":True,"camera":"QA_ORTHOGRAPHIC_NON_CANON","render_engine":"BLENDER_WORKBENCH","polygon_count":len(obj.data.polygons),"png_sha256":hashlib.sha256(png.read_bytes()).hexdigest()}
    (out/"render_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    print("TECHNICAL_RENDER_PASS",flush=True)
if __name__=="__main__":main()
