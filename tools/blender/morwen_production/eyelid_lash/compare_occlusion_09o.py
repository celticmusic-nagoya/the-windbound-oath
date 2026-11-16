"""09O: controlled 09N visibility comparison with identical camera and geometry.

Separates root mesh appearance from cage occlusion. Diagnostic only.
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
    if len(dst.objects)!=18 or any(o is None for o in dst.objects):raise ValueError("18 candidate strips required")
    for o in dst.objects:
        if not o.users_collection:bpy.context.collection.objects.link(o)
        o.hide_set(False)
        o.hide_viewport=False
    lash=bpy.data.objects["M09_L_LASH_CANDIDATE_00"]
    cage=bpy.data.objects["M08_L_CONTACT_CAGE_050"]
    for ob in (lash,cage):
        for collection in ob.users_collection:collection.hide_render=False
    verts=[lash.matrix_world@v.co for v in lash.data.vertices]
    root=sum(verts[:3],Vector())/3
    extent=max((v-root).length for v in verts)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.film_transparent=False
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="OBJECT"
    lash.color=(0.05,0.02,0.01,1)
    cage.color=(0.73,0.56,0.45,1)
    bpy.ops.object.camera_add()
    cam=bpy.context.object
    cam.data.type="ORTHO"
    cam.data.clip_start=0.0001
    cam.data.clip_end=100
    cam.data.ortho_scale=max(extent*2,0.003)
    scene.camera=cam
    a.outdir.mkdir(parents=True)
    results=[]
    for direction in ("front","oblique","side"):
        vector={"front":(0,-1,0.2),"oblique":(1,-1,0.7),"side":(1,-0.25,0.2)}[direction]
        cam.location=root+Vector(vector).normalized()*max(extent*12,0.08)
        cam.rotation_euler=(root-cam.location).to_track_quat("-Z","Y").to_euler()
        for mode in ("lash_only","cage_and_lash"):
            visible={lash.name} if mode=="lash_only" else {lash.name,cage.name}
            for o in bpy.data.objects:
                if o.type=="MESH":o.hide_render=o.name not in visible
            bpy.context.view_layer.update()
            name=direction+"_"+mode
            path=a.outdir/(name+".png")
            scene.render.filepath=str(path.resolve())
            bpy.ops.render.render(write_still=True)
            if not path.exists() or not path.stat().st_size:raise ValueError("Missing image "+name)
            results.append({"name":name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    report={"status":"DIAGNOSTIC_UNAPPROVED","views":results,
      "model_sha256":hashlib.sha256(a.model.read_bytes()).hexdigest(),
      "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "camera_identical_within_view":True,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"DIAGNOSTIC_ONLY","G4":"NOT_RUN"}
    (a.outdir/"RENDER_MANIFEST_09O.json").write_text(json.dumps(report,indent=2)+"\n")
    print("M09_OCCLUSION_09O="+json.dumps({"status":report["status"],"views":len(results)}),flush=True)
if __name__=="__main__":main()
