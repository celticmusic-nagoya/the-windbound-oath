"""CPU-only four-view torso clay renders for independent shape review."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/"assets/candidates/morwen-blender-15/morwen_anatomical_torso_candidate.blend"
OUT=ROOT/"assets/candidates/morwen-blender-16"
VIEWS={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}
def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene=bpy.context.scene
    body=bpy.data.objects["Morwen_15_anatomical_torso_candidate"]
    for ob in scene.objects:
        if ob.type=="MESH":ob.hide_render=(ob!=body)
    body.hide_render=False
    coords=[body.matrix_world@v.co for v in body.data.vertices]
    mins=Vector(tuple(min(p[i] for p in coords) for i in range(3)))
    maxs=Vector(tuple(max(p[i] for p in coords) for i in range(3)))
    center=(mins+maxs)/2
    span=maxs-mins
    assert span.z>0 and span.x>0 and span.y>0
    mat=bpy.data.materials.new("Morwen_16_neutral_clay")
    mat.diffuse_color=(.48,.54,.60,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(.48,.54,.60,1)
    bsdf.inputs["Roughness"].default_value=.9
    body.data.materials.clear()
    body.data.materials.append(mat)
    camera_data=bpy.data.cameras.new("Morwen_16_ortho")
    camera=bpy.data.objects.new("Morwen_16_ortho",camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera_data.type="ORTHO"
    # Landscape horizontal extent must fit portrait frame.
    camera_data.ortho_scale=max(span.z/.72,span.x/.27,span.y/.27)*1.1
    light_data=bpy.data.lights.new("Morwen_16_area","AREA")
    light=bpy.data.objects.new("Morwen_16_area",light_data)
    scene.collection.objects.link(light)
    light.location=center+Vector((2,-3,5))
    light_data.energy=650
    light_data.shape="DISK"
    light_data.size=5
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=12
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles"):
            layer.cycles.use_denoising=False
    scene.render.resolution_x=384
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=True
    OUT.mkdir(parents=True,exist_ok=True)
    names=[]
    for facing,direction in VIEWS.items():
        camera.location=center+Vector(direction)*10
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        path=OUT/(facing+"_torso_clay.png")
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        assert path.stat().st_size>1000,path
        names.append(path.name)
    report={"task":"MORWEN-BLENDER-16","renders":names,
            "count":len(names),"source":"MORWEN-BLENDER-15",
            "clay_only":True,"full_body":False,"visual_art_qa":"NOT_RUN",
            "production_use":False}
    (OUT/"render_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_16_TORSO_CLAY_RENDER_PASS")
if __name__=="__main__":main()
