"""09I candidate-only Blender contact sheet renders; visual QA remains human-reviewed."""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True,type=Path)
    p.add_argument("--strips",required=True,type=Path)
    p.add_argument("--outdir",required=True,type=Path)
    a=p.parse_args()
    if a.outdir.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18:raise ValueError("Expected 18 strips")
    for ob in dst.objects:
        if ob is None:raise ValueError("Missing lash")
        if not ob.users_collection:bpy.context.collection.objects.link(ob)
    wanted={"M08_L_CONTACT_CAGE_050","M08_R_CONTACT_CAGE_050","MORWEN_Eyes"}
    for ob in bpy.data.objects:
        if ob.type=="MESH":
            ob.hide_render=not(ob.name in wanted or ob.name.startswith("M09_") and "_LASH_CANDIDATE_" in ob.name)
    coords=[ob.matrix_world@v.co for ob in dst.objects for v in ob.data.vertices]
    if not coords:raise ValueError("Empty geometry")
    lo=Vector([min(v[i] for v in coords) for i in range(3)])
    hi=Vector([max(v[i] for v in coords) for i in range(3)])
    center=(lo+hi)*0.5
    extent=max((hi-lo).length,0.015)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.film_transparent=True
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.camera=None
    bpy.ops.object.camera_add()
    camera=bpy.context.object
    camera.name="M09I_DIAGNOSTIC_CAMERA"
    camera.data.type="ORTHO"
    camera.data.ortho_scale=extent*1.5
    scene.camera=camera
    a.outdir.mkdir(parents=True)
    outputs=[]
    for label,vec in (("front",(0,-1,0.15)),("side",(1,-0.4,0.15)),("oblique",(1,-1,0.65))):
        direction=Vector(vec).normalized()
        camera.location=center+direction*extent*2.5
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        path=a.outdir/(label+".png")
        scene.render.filepath=str(path.resolve())
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size==0:raise ValueError("Missing render "+label)
        outputs.append({"view":label,"filename":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    report={"status":"RENDERED_UNAPPROVED_CANDIDATE","model_sha256":hashlib.sha256(a.model.read_bytes()).hexdigest(),
       "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),"engine":"BLENDER_WORKBENCH",
       "views":outputs,"G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_ONLY","G4":"NOT_RUN"}
    (a.outdir/"RENDER_MANIFEST_09I.json").write_text(json.dumps(report,indent=2)+"\n")
    print("M09_RENDER_09I="+json.dumps({"status":report["status"],"views":len(outputs)}),flush=True)
if __name__=="__main__":main()
