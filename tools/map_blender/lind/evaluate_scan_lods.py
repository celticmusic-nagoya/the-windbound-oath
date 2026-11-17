"""Non-destructive LOD evaluation of the actual scanned cliff source.

The full original glTF remains unmodified. A separate Blender scene and render
compare full and reduced triangles; no acceptance or world collision claim.
"""
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def render(scene,obj,center,span,out,name):
    camera=bpy.data.cameras.new("LOD_QA_CAM_"+name)
    cam=bpy.data.objects.new("LOD_QA_CAM_"+name,camera)
    bpy.context.collection.objects.link(cam)
    cam.location=center+Vector((span*.55,-span*1.8,span*.48))
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    camera.type="ORTHO";camera.ortho_scale=span*1.65
    scene.camera=cam
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_cavity=True
    scene.render.resolution_x=1024;scene.render.resolution_y=720
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
    return {"file":name+".png","sha256":digest(out/(name+".png"))}

def main():
    argv=sys.argv[sys.argv.index("--")+1:]
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True)
    a=ap.parse_args(argv)
    out=Path(a.out).resolve()
    source=out/"sources/coastal_cliff_04/coastal_cliff_04_1k.gltf"
    assert source.exists()
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if len(meshes)!=1: raise RuntimeError("Unexpected publisher source mesh count")
    original=meshes[0]
    original.name="SOURCE_SCAN_FULL_UNMODIFIED"
    original.hide_render=False
    original_tri=sum(len(p.vertices)-2 for p in original.data.polygons)
    if original_tri<1000000:raise RuntimeError("Unexpected source mesh")
    coords=[original.matrix_world@Vector(c) for c in original.bound_box]
    center=sum(coords,Vector())/len(coords)
    span=max(max(p[i] for p in coords)-min(p[i] for p in coords) for i in range(3))
    scene=bpy.context.scene
    result={"source_glTF_sha256":digest(source),"source_triangles":original_tri,
      "candidate_status":"NON_ADOPTED_LOD_TECHNICAL_STUDY",
      "target_ratios":[0.25,0.10],
      "views":{},"lods":[],
      "G1":"BLOCKED_WORLD_ALIGNMENT","G2":"NOT_RUN_INDEPENDENT","G3":"TECHNICAL_ONLY","G4":"NOT_RUN"}
    result["views"]["full"]=render(scene,original,center,span,out,"full")
    original.hide_render=True;original.hide_set(True)
    for ratio in result["target_ratios"]:
        candidate=original.copy()
        candidate.data=original.data.copy()
        bpy.context.collection.objects.link(candidate)
        candidate.hide_render=False;candidate.hide_set(False)
        candidate.name="SCAN_LOD_"+str(round(ratio*100))
        bpy.ops.object.select_all(action="DESELECT")
        candidate.select_set(True);bpy.context.view_layer.objects.active=candidate
        dec=candidate.modifiers.new("NONDESTRUCTIVE_LOD","DECIMATE")
        dec.ratio=ratio
        bpy.ops.object.modifier_apply(modifier=dec.name)
        triangles=sum(len(p.vertices)-2 for p in candidate.data.polygons)
        if not 0<triangles<original_tri:raise RuntimeError("LOD failed")
        label="lod_"+str(round(ratio*100))
        result["views"][label]=render(scene,candidate,center,span,out,label)
        result["lods"].append({"ratio":ratio,"triangles":triangles,"vertices":len(candidate.data.vertices),
           "uv_layers":len(candidate.data.uv_layers),"candidate_object":candidate.name})
        candidate.hide_render=True;candidate.hide_set(True)
    original.hide_set(False)
    for o in meshes: o.hide_render=False
    for o in bpy.data.objects:
        if o.name.startswith("SCAN_LOD_"):o.hide_render=True
    bpy.ops.file.pack_all()
    blend=out/"scan_lod_comparison.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    result["blend"]={"file":blend.name,"sha256":digest(blend)}
    (out/"lod_qa.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SCAN_LOD_TECH_PASS",original_tri,[v["triangles"] for v in result["lods"]])
if __name__=="__main__":main()
