"""Candidate-only orthographic render + glTF smoke test for Morwen Blender-24.
Usage: blender -b -noaudio --python tools/blender/morwen_blender_26/render_and_export.py
"""
import json, math, os
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"assets/candidates/morwen-blender-24/morwen_anatomical_torso_candidate.blend"
OUT=ROOT/"assets/candidates/morwen-blender-26"
def main():
    assert SRC.is_file(), "Missing BLENDER-24 candidate .blend"
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    target=next((o for o in bpy.data.objects if o.type=="MESH" and "Morwen_24_" in o.name),None)
    assert target is not None,"Candidate torso object missing"
    OUT.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=16
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):
            layer.cycles.use_denoising=False
    scene.use_nodes=False
    scene.render.resolution_x=512;scene.render.resolution_y=768
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    mat=bpy.data.materials.new("QA_neutral_clay")
    mat.diffuse_color=(.62,.65,.69,1)
    mat.use_nodes=True
    principled=mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value=(.62,.65,.69,1)
    principled.inputs["Roughness"].default_value=.8
    target.data.materials.clear();target.data.materials.append(mat)
    for obj in bpy.context.selected_objects:obj.select_set(False)
    target.select_set(True);bpy.context.view_layer.objects.active=target
    center=sum((target.matrix_world@Vector(v.co) for v in target.data.vertices),Vector())/len(target.data.vertices)
    dims=target.dimensions
    # Ortho scale is vertical coverage; fit projected bbox per view below.
    scale=max(dims.x,dims.y,dims.z)*1.55
    camdata=bpy.data.cameras.new("QA_orthographic_camera")
    camera=bpy.data.objects.new("QA_orthographic_camera",camdata)
    scene.collection.objects.link(camera);scene.camera=camera
    camdata.type="ORTHO";camdata.ortho_scale=scale
    lightdata=bpy.data.lights.new("QA_softbox","AREA")
    light=bpy.data.objects.new("QA_softbox",lightdata)
    scene.collection.objects.link(light)
    light.location=center+Vector((.8,-1.2,1.4))
    lightdata.energy=400;lightdata.shape="DISK";lightdata.size=3
    views={"front":(0,-1,0),"left":(-1,0,0),"right":(1,0,0),
           "back":(0,1,0),"three_quarter":(.8,-1,0.35)}
    files=[]
    smoke_only=os.environ.get("MORWEN_SMOKE_ONLY")=="1"
    for name,direction in views.items():
        direction=Vector(direction).normalized()
        camera.location=center+direction*2.0
        quat=(center-camera.location).to_track_quat("-Z","Y")
        camera.rotation_euler=quat.to_euler()
        # Fit actual transformed vertices to camera frame with a 15% margin.
        q=camera.rotation_euler.to_quaternion().inverted()
        projected=[q@(target.matrix_world@v.co-center) for v in target.data.vertices]
        width=max(v.x for v in projected)-min(v.x for v in projected)
        height=max(v.y for v in projected)-min(v.y for v in projected)
        aspect=scene.render.resolution_x/scene.render.resolution_y
        camdata.ortho_scale=max(height,width/aspect)*1.3
        # Shift toward bounding-box center, not vertex-density center.
        offset=Vector(((max(v.x for v in projected)+min(v.x for v in projected))/2,
                       (max(v.y for v in projected)+min(v.y for v in projected))/2,0))
        camera.location+=camera.rotation_euler.to_quaternion()@offset
        scene.render.filepath=str(OUT/(name+".png"))
        bpy.ops.render.render(write_still=True)
        assert (OUT/(name+".png")).stat().st_size>1000
        files.append(name+".png")
        if smoke_only:
            break
    if os.environ.get("MORWEN_RENDER_ONLY") != "1" and not smoke_only:
        bpy.ops.export_scene.gltf(filepath=str(OUT/"morwen_torso_candidate.glb"),
           export_format="GLB",use_selection=True)
        assert (OUT/"morwen_torso_candidate.glb").stat().st_size>1000
    report={"task":"MORWEN-BLENDER-26","art_approval":"NOT_RUN",
      "source_candidate":"BLENDER-24","render_views":files,
      "glb":None if os.environ.get("MORWEN_RENDER_ONLY") == "1" or smoke_only else "morwen_torso_candidate.glb","production_use":False}
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_26_RENDER_EXPORT_PASS")
if __name__=="__main__":main()
