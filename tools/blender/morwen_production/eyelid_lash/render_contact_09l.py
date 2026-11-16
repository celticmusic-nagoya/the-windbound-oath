"""09L diagnostic: lash-to-lid contact closeups and small display-size previews.

Candidate-only. Render separate isolated root, cage+root and all lashes+cage;
does not alter canonical assets or certify aesthetic quality.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    for key in ("model","strips","outdir"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    if a.outdir.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18 or any(o is None for o in dst.objects):raise ValueError("18 lashes required")
    for o in dst.objects:
        if not o.users_collection:bpy.context.collection.objects.link(o)
        o.hide_set(False)
        o.hide_viewport=False
    lash=bpy.data.objects["M09_L_LASH_CANDIDATE_00"]
    cage=bpy.data.objects["M08_L_CONTACT_CAGE_050"]
    for o in (lash,cage):
        for collection in o.users_collection:collection.hide_render=False
    points=[lash.matrix_world@v.co for v in lash.data.vertices]
    root=sum(points[:3],Vector())/3
    extent=max((v-root).length for v in points)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.film_transparent=False
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="OBJECT"
    lash.color=(0.04,0.02,0.015,1)
    cage.color=(0.73,0.56,0.45,1)
    bpy.ops.object.camera_add()
    cam=bpy.context.object
    cam.data.type="ORTHO"
    cam.data.clip_start=0.0001
    cam.data.clip_end=100
    scene.camera=cam
    a.outdir.mkdir(parents=True)
    results=[]
    views=[
        ("contact_front",root,(0,-1,0.2),max(extent*2,0.003),{"M09_L_LASH_CANDIDATE_00","M08_L_CONTACT_CAGE_050"},1024),
        ("contact_oblique",root,(1,-1,0.7),max(extent*2,0.003),{"M09_L_LASH_CANDIDATE_00","M08_L_CONTACT_CAGE_050"},1024),
        ("contact_side",root,(1,-0.25,0.2),max(extent*2,0.003),{"M09_L_LASH_CANDIDATE_00","M08_L_CONTACT_CAGE_050"},1024),
        ("display_48px",root,(1,-1,0.7),max(extent*5,0.01),{"M09_L_LASH_CANDIDATE_00","M08_L_CONTACT_CAGE_050"},48),
    ]
    for name,target,view,scale,visible,res in views:
        for o in bpy.data.objects:
            if o.type=="MESH":o.hide_render=o.name not in visible
        cam.location=target+Vector(view).normalized()*max(extent*12,0.08)
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.ortho_scale=scale
        scene.render.resolution_x=res
        scene.render.resolution_y=res
        bpy.context.view_layer.update()
        path=a.outdir/(name+".png")
        scene.render.filepath=str(path.resolve())
        bpy.ops.render.render(write_still=True)
        if not path.exists() or path.stat().st_size==0:raise RuntimeError("Empty file "+name)
        img=bpy.data.images.load(str(path.resolve()),check_existing=False)
        try:
            pixels=img.pixels[:]
            rgbmin=min(pixels[0::4])
            rgbmax=max(pixels[0::4])
            if rgbmax-rgbmin<0.005:raise RuntimeError("Uniform red channel "+name)
        finally:bpy.data.images.remove(img)
        results.append({"view":name,"resolution":res,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    report={"status":"RENDERED_UNAPPROVED_CONTACT_DIAGNOSTICS","views":results,
      "model_sha256":hashlib.sha256(a.model.read_bytes()).hexdigest(),
      "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_ONLY","G4":"NOT_RUN"}
    (a.outdir/"RENDER_MANIFEST_09L.json").write_text(json.dumps(report,indent=2)+"\n")
    print("M09_RENDER_09L="+json.dumps({"status":report["status"],"views":len(results)}),flush=True)
if __name__=="__main__":main()
