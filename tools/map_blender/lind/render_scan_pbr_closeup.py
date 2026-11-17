"""Close-up PBR material QA for actual Poly Haven cliff source and 25% LOD.

Does not alter official CG or the verified scan original. Camera is shared,
lighting is reproducible, and render hashes are retained.
"""
import argparse, bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def render(scene,obj,cam,target,output,name):
    camera=bpy.data.cameras.new("CLOSEUP_"+name)
    camera.type="ORTHO"
    camera.ortho_scale=11.0
    camera.clip_end=1000
    co=bpy.data.objects.new("CLOSEUP_"+name,camera)
    bpy.context.collection.objects.link(co)
    co.location=cam
    co.rotation_euler=(target-co.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=co
    scene.render.filepath=str(output/(name+".png"))
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(co,do_unlink=True)
    return {"file":name+".png","sha256":digest(output/(name+".png"))}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    args=ap.parse_args(sys.argv[sys.argv.index("--")+1:])
    out=Path(args.out).resolve()
    original=out/"sources/coastal_cliff_04/coastal_cliff_04_1k.gltf"
    assert original.is_file()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(original))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if len(meshes)!=1:raise RuntimeError("Expected one scanned mesh object")
    source=meshes[0]
    source.name="SOURCE_FULL_PBR_UNMODIFIED"
    ntri=sum(len(p.vertices)-2 for p in source.data.polygons)
    if ntri<1000000 or len(source.data.uv_layers)<1:raise RuntimeError("Missing source geometry/UV")
    lod=source.copy()
    lod.data=source.data.copy()
    bpy.context.collection.objects.link(lod)
    lod.name="LOD25_PBR_CANDIDATE"
    bpy.ops.object.select_all(action="DESELECT")
    lod.select_set(True)
    bpy.context.view_layer.objects.active=lod
    modifier=lod.modifiers.new("LOD25_DECIMATE","DECIMATE")
    modifier.ratio=.25
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    lodtri=sum(len(p.vertices)-2 for p in lod.data.polygons)
    if not 0<lodtri<ntri or len(lod.data.uv_layers)<1:raise RuntimeError("LOD UV failure")
    # Source scan extends roughly x=-47..39, y=-15..9, z=-.65..10.35.
    # This is a fixed DIAGNOSTIC camera, not the approved game camera.
    target=Vector((-5.0,-4.0,4.4))
    camera=Vector((-1.0,-24.0,11.0))
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
    scene.render.resolution_x=1200
    scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    if hasattr(scene,"eevee"):scene.eevee.taa_render_samples=32
    world=bpy.data.worlds.new("PBR_QA_WORLD")
    scene.world=world
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.7,.73,.78,1)
    bg.inputs["Strength"].default_value=.8
    ld=bpy.data.lights.new("PBR_QA_AREA","AREA")
    light=bpy.data.objects.new("PBR_QA_AREA",ld)
    bpy.context.collection.objects.link(light)
    light.location=Vector((-9,-16,22))
    light.rotation_euler=(target-light.location).to_track_quat("-Z","Y").to_euler()
    ld.energy=4500
    ld.size=12
    # Extra fill helps see normal/roughness rather than a nearly black scan.
    fill_data=bpy.data.lights.new("PBR_QA_FILL","AREA")
    fill=bpy.data.objects.new("PBR_QA_FILL",fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location=Vector((9,-10,15))
    fill.rotation_euler=(target-fill.location).to_track_quat("-Z","Y").to_euler()
    fill_data.energy=2500
    fill_data.size=15
    source.hide_render=False;lod.hide_render=True
    full=render(scene,source,camera,target,out,"pbr_closeup_full")
    source.hide_render=True;lod.hide_render=False
    reduced=render(scene,lod,camera,target,out,"pbr_closeup_lod25")
    # No permanent changes to the publisher's source glTF.
    source.hide_render=False;lod.hide_render=True
    bpy.ops.file.pack_all()
    blend=out/"scan_pbr_closeup_study.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    result={"source_glTF_sha256":digest(original),"source_triangles":ntri,
      "lod25_triangles":lodtri,"uv_source":len(source.data.uv_layers),
      "uv_lod":len(lod.data.uv_layers),
      "blender_version":bpy.app.version_string,
      "render_resolution":[1200,800],
      "fixed_diagnostic_camera":{"location":list(camera),"target":list(target),"ortho_scale":11.0},
      "lighting":{"key_watts":4500,"fill_watts":2500,"world_strength":.8},
      "images":{"full":full,"lod25":reduced},
      "blend":{"file":blend.name,"sha256":digest(blend)},
      "G1":"BLOCKED_WORLD_ALIGNMENT","G2":"NOT_RUN_INDEPENDENT",
      "G3":"TECHNICAL_CHECK_PENDING","G4":"NOT_RUN",
      "source_status":"UNMODIFIED_ORIGINAL_AND_SEPARATE_LOD"}
    (out/"pbr_closeup_qa.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PBR_CLOSEUP_RENDER_COMPLETE",ntri,lodtri)
if __name__=="__main__":main()
