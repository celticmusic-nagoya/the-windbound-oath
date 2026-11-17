#!/usr/bin/env python3
"""Create a reproducible renderable Blender stage from a CC0 body basemesh.

This is an anatomy/proportion staging asset, NOT the canonical Morwen character.
No costume, hair, face design, or anatomy acceptance is implied.
"""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector

NAME="GEO-body_female_realistic"
VIEWS={"front":(0,-1,0),"left":(-1,0,0),"back":(0,1,0),"right":(1,0,0)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();src=pathlib.Path(a.source).resolve();out=pathlib.Path(a.output).resolve()
    if not src.is_file() or src==out or src.is_relative_to(out) or out.is_relative_to(src):
        raise SystemExit("BLOCKED invalid source/output")
    original_hash=hashlib.sha256(src.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    ob=bpy.data.objects.get(NAME)
    if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED missing female realistic source mesh")
    verts=[ob.matrix_world@v.co for v in ob.data.vertices]
    low=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
    mesh=ob.data.copy();world=ob.matrix_world.copy()
    bpy.ops.object.select_all(action="SELECT")
    for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
    stage=bpy.data.objects.new("MORWEN_PROPORTION_STAGE_UNAPPROVED",mesh)
    bpy.context.scene.collection.objects.link(stage);stage.matrix_world=world
    stage["status"]="CANDIDATE_BASEMESH_ONLY_NOT_MORWEN"
    stage["source_sha256"]=original_hash
    stage["target_heads"]=7.75
    stage["head_ratio_verified"]=False
    stage["costume_modelled"]=False
    stage["canonical_approval"]=False
    mat=bpy.data.materials.new("neutral_proportion_clay")
    mat.diffuse_color=(0.48,0.43,0.57,1)
    mat.use_nodes=True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.48,0.43,0.57,1)
    mesh.materials.clear();mesh.materials.append(mat)
    sc=bpy.context.scene
    sc.render.engine="BLENDER_EEVEE_NEXT"
    sc.render.resolution_x=768;sc.render.resolution_y=1024
    sc.render.resolution_percentage=100
    sc.render.film_transparent=True
    sc.render.image_settings.file_format="PNG"
    sc.render.image_settings.color_mode="RGBA"
    sc.render.image_settings.color_depth="8"
    sc.view_settings.view_transform="Standard"
    center=(low+high)*0.5;size=high-low
    world_data=bpy.data.worlds.new("neutral_stage_world");world_data.use_nodes=True
    world_data.node_tree.nodes["Background"].inputs["Color"].default_value=(0.45,0.45,0.45,1)
    world_data.node_tree.nodes["Background"].inputs["Strength"].default_value=0.8
    sc.world=world_data
    for label,offset,power in (("key",(1.5,-2.0,2.5),700),("fill",(-1.5,-1.0,1.0),400),("rim",(0,2.0,2.0),550)):
        data=bpy.data.lights.new(label,"AREA");data.energy=power;data.shape="DISK";data.size=3
        lamp=bpy.data.objects.new(label,data);sc.collection.objects.link(lamp)
        lamp.location=center+Vector(offset)*max(size.z,1)
        lamp.rotation_euler=(center-lamp.location).to_track_quat("-Z","Y").to_euler()
    camera_data=bpy.data.cameras.new("orthographic_4view");camera=bpy.data.objects.new("orthographic_4view",camera_data)
    sc.collection.objects.link(camera);sc.camera=camera;camera_data.type="ORTHO";camera_data.ortho_scale=2.05
    out.mkdir(parents=True,exist_ok=True)
    evidence={"status":"PROPORTION_STAGE_ONLY","source_sha256":original_hash,
              "mesh":NAME,"blender":bpy.app.version_string,
              "target_heads":7.75,"actual_heads":"UNVERIFIED",
              "canonical_design_match":"BLOCKED","independent_art_qa":"NOT_RUN",
              "rig_qa":"NOT_RUN","game_qa":"NOT_RUN","views":[]}
    for view,direction in VIEWS.items():
        camera.location=center+Vector(direction)*max(size)*3
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        png=out/("proportion_stage_"+view+".png")
        sc.render.filepath=str(png);bpy.ops.render.render(write_still=True)
        evidence["views"].append({"view":view,"file":png.name,"sha256":hashlib.sha256(png.read_bytes()).hexdigest()})
    camera.location=center+Vector((0,-1,0))*max(size)*3
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    blend=out/"morwen_proportion_stage_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    evidence["blend_sha256"]=hashlib.sha256(blend.read_bytes()).hexdigest()
    evidence["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==original_hash
    if not evidence["source_unchanged"]:raise SystemExit("FAIL original source changed")
    (out/"stage_manifest.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"status":evidence["status"],"render_count":len(evidence["views"]),"blend_bytes":blend.stat().st_size}))
if __name__=="__main__":main()
