"""BLENDER-34: isolate candidate mesh from inherited Blender scene and render front RGBA diagnostic."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"assets/candidates/morwen-blender-24/morwen_anatomical_torso_candidate.blend"
OUT=ROOT/"assets/candidates/morwen-blender-34"

def main():
    assert SRC.is_file(), f"missing {SRC}"
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    original=[{"name":o.name,"type":o.type,"hide_render":o.hide_render}
              for o in bpy.data.objects]
    target=next((o for o in bpy.data.objects if o.type=="MESH" and "Morwen_24_" in o.name),None)
    assert target is not None,"candidate mesh missing"
    coords=[target.matrix_world@v.co for v in target.data.vertices]
    assert coords,"candidate mesh empty"
    mins=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    maxs=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    center=(mins+maxs)/2
    OUT.mkdir(parents=True,exist_ok=True)

    # Fresh scene, object allowlist. Copy mesh data so no production file is altered.
    scene=bpy.data.scenes.new("Morwen_34_isolated_diagnostic")
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=12
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):
            layer.cycles.use_denoising=False
    scene.use_nodes=False
    scene.render.film_transparent=True
    scene.render.resolution_x=512
    scene.render.resolution_y=768
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.color_depth="8"
    scene.world=bpy.data.worlds.new("Morwen_34_world")

    isolated=bpy.data.objects.new("Morwen_34_torso_only",target.data.copy())
    isolated.matrix_world=target.matrix_world.copy()
    scene.collection.objects.link(isolated)
    mat=bpy.data.materials.new("Morwen_34_neutral_clay")
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(.62,.65,.69,1)
    shader.inputs["Roughness"].default_value=.8
    isolated.data.materials.clear()
    isolated.data.materials.append(mat)

    camdata=bpy.data.cameras.new("Morwen_34_camera")
    camera=bpy.data.objects.new("Morwen_34_camera",camdata)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera.location=center+Vector((0,-max((maxs-mins).length,1)*2,0))
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    camdata.type="ORTHO"
    camdata.ortho_scale=max((maxs.z-mins.z)*1.35,(maxs.x-mins.x)*1.35*768/512,0.1)

    lightdata=bpy.data.lights.new("Morwen_34_area","AREA")
    light=bpy.data.objects.new("Morwen_34_area",lightdata)
    scene.collection.objects.link(light)
    light.location=center+Vector((1,-2,3))
    lightdata.energy=500
    lightdata.size=4

    bpy.context.window.scene=scene
    scene.render.filepath=str(OUT/"front_isolated.png")
    bpy.ops.render.render(write_still=True,scene=scene.name)
    output=OUT/"front_isolated.png"
    assert output.is_file() and output.stat().st_size>1000
    report={"task":"BLENDER-34","source":str(SRC.relative_to(ROOT)),
            "source_objects":original,"isolated_objects":[o.name for o in scene.objects],
            "render":output.name,"art_approval":"NOT_RUN","production_use":False}
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_34_ISOLATED_RENDER_PASS")

if __name__=="__main__":
    main()
