"""MORWEN-BLENDER-05: render four orthographic projection contact sheets.
Neutral 3D candidate only. Does not modify source or certify artistic match.
"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-05"
RIG="Morwen_unified_17_candidate"
BODY="Morwen_unified_neutral_3d_candidate"
VIEWS={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}

def main():
    scene=bpy.context.scene
    rig=bpy.data.objects[RIG]
    body=bpy.data.objects[BODY]
    assert len(rig.data.bones)==17
    assert len(body.vertex_groups)==16
    # Exclude the four independent source-view blockouts from rendering.
    for obj in scene.objects:
        obj.hide_render=obj not in (rig,body) and obj.type=="MESH"
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=8
    scene.render.resolution_x=384
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    scene.camera=None
    camdata=bpy.data.cameras.new("MORWEN_05_ORTHOGRAPHIC_QA")
    cam=bpy.data.objects.new(camdata.name,camdata)
    scene.collection.objects.link(cam)
    scene.camera=cam
    camdata.type="ORTHO"
    # Camera center and orthographic span based on neutral candidate mesh,
    # identical scale and center for all directions.
    deps=bpy.context.evaluated_depsgraph_get()
    deps.update()
    evaluated=body.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    try:
        coords=[body.matrix_world @ v.co for v in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()
    center=sum(coords,Vector())/len(coords)
    extent=max(max(v.z for v in coords)-min(v.z for v in coords),0.1)
    camdata.ortho_scale=extent*1.15
    OUT.mkdir(parents=True,exist_ok=True)
    paths={}
    for facing,direction in VIEWS.items():
        direction=Vector(direction)
        cam.location=center+direction*10
        cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath=str(OUT/(facing+"_projection.png"))
        bpy.ops.render.render(write_still=True)
        paths[facing]=scene.render.filepath
        assert Path(scene.render.filepath).stat().st_size>1000
    report={"task":"MORWEN-BLENDER-05","status":"PROJECTION_RENDERED_TECHNICAL_ONLY",
            "view_order":list(VIEWS),"resolution":[384,1024],
            "projection":"ORTHOGRAPHIC","ortho_scale":camdata.ortho_scale,
            "camera_center":list(center),"images":paths,
            "visual_reference_comparison":"NOT_RUN",
            "anatomy_approval":"NOT_RUN","continuous_skin":False,
            "production_use":False}
    (OUT/"projection_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_BLENDER_05_RENDER_PASS")

if __name__=="__main__":
    main()
