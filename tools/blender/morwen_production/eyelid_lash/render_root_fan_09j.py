"""09J: isolated lash-root closeups to remove 09I cage/eye occlusion.

Diagnostic candidate renders only. Separate root closeup and whole-lash views;
no claim of artistic acceptance or full-character reference matching.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    for k in ("model","strips","outdir"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.outdir.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18:raise ValueError("Expected 18 lashes")
    for ob in dst.objects:
        if ob is None:raise ValueError("Missing lash")
        if not ob.users_collection:bpy.context.collection.objects.link(ob)
        ob.hide_set(False)
        ob.hide_viewport=False
        ob.hide_render=False
    lash=bpy.data.objects["M09_L_LASH_CANDIDATE_00"]
    for collection in lash.users_collection:
        collection.hide_render=False
    lash.hide_render=False
    for ob in bpy.data.objects:
        if ob.type=="MESH":ob.hide_render=ob!=lash
    world=[lash.matrix_world@v.co for v in lash.data.vertices]
    if len(world)!=9:raise ValueError("Unexpected 09G fan topology")
    center=sum(world,Vector())/len(world)
    root=(world[0]+world[1]+world[2])/3
    extent=max((v-center).length for v in world)*2
    root_extent=max((v-root).length for v in world[:5])*2
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.film_transparent=True
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    bpy.ops.object.camera_add()
    camera=bpy.context.object
    camera.data.type="ORTHO"
    camera.data.clip_start=0.0001
    scene.camera=camera
    a.outdir.mkdir(parents=True)
    outputs=[]
    for label,target,scale,vec in (
        ("root_front",root,root_extent,(0,-1,0.2)),
        ("root_side",root,root_extent,(1,-0.5,0.2)),
        ("root_oblique",root,root_extent,(1,-1,0.8)),
        ("whole_lash",center,extent,(1,-1,0.8)),
    ):
        direction=Vector(vec).normalized()
        camera.location=target+direction*max(extent,0.015)*3
        camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
        camera.data.ortho_scale=max(scale*1.5,0.001)
        bpy.context.view_layer.update()
        path=a.outdir/(label+".png")
        scene.render.filepath=str(path.resolve())
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size==0:raise ValueError("Missing "+label)
        image=bpy.data.images.load(str(path.resolve()),check_existing=False)
        try:
            alpha=image.pixels[3::4]
            if max(alpha,default=0.0)<=0.001:raise ValueError("Fully transparent render "+label)
        finally:bpy.data.images.remove(image)
        outputs.append({"view":label,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    report={"status":"DIAGNOSTIC_ONLY_UNAPPROVED","rendered_views":outputs,
        "eye_and_cage_hidden":True,"lash_object":"M09_L_LASH_CANDIDATE_00",
        "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_ONLY","G4":"NOT_RUN"}
    (a.outdir/"RENDER_MANIFEST_09J.json").write_text(json.dumps(report,indent=2)+"\n")
    print("M09_RENDER_09J="+json.dumps({"views":len(outputs),"status":report["status"]}),flush=True)
if __name__=="__main__":main()
