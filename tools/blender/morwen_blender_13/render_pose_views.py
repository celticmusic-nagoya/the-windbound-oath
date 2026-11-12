"""Render Morwen connected candidate in four neutral views and two joint poses."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-13"
VIEWS={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}
POSES={"neutral":{},"arms_bent":{"forearm.L":.55,"forearm.R":-.55},"walking":{"thigh.L":.35,"thigh.R":-.35,"shin.L":-.25,"shin.R":.25}}

def main():
    scene=bpy.context.scene
    rig=bpy.data.objects["Morwen_unified_17_candidate"]
    body=bpy.data.objects["Morwen_11_voxel_union_candidate"]
    assert len(rig.data.bones)==17
    for obj in scene.objects:
        if obj.type in {"MESH","CURVE","FONT","SURFACE"}:
            obj.hide_render=(obj!=body)
    body.hide_render=False
    coords=[body.matrix_world@v.co for v in body.data.vertices]
    mins=Vector(tuple(min(p[i] for p in coords) for i in range(3)))
    maxs=Vector(tuple(max(p[i] for p in coords) for i in range(3)))
    center=(mins+maxs)/2
    span=maxs-mins
    ortho=max(span.z/.70,max(span.x,span.y)/(.375*.70))*1.15
    camera_data=bpy.data.cameras.new("Morwen_13_camera")
    camera=bpy.data.objects.new("Morwen_13_camera",camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera;camera_data.type="ORTHO";camera_data.ortho_scale=ortho
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=384;scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    scene.world.color=(.8,.8,.8)
    OUT.mkdir(parents=True,exist_ok=True)
    files=[]
    for pose,rotations in POSES.items():
        for bone in rig.pose.bones:
            bone.rotation_mode="XYZ";bone.rotation_euler=(0,0,0)
        for name,angle in rotations.items():
            rig.pose.bones[name].rotation_euler.x=angle
        bpy.context.view_layer.update()
        for facing,direction in VIEWS.items():
            camera.location=center+Vector(direction)*10
            camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
            path=OUT/(pose+"_"+facing+".png")
            scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            assert path.exists() and path.stat().st_size>1000
            files.append(path.name)
    for bone in rig.pose.bones:bone.rotation_euler=(0,0,0)
    report={"task":"MORWEN-BLENDER-13","renders":files,"count":len(files),
            "reference_images_modified":False,"visual_art_qa":"NOT_RUN",
            "production_use":False}
    (OUT/"render_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_13_POSE_RENDERS_PASS")

if __name__=="__main__":main()
