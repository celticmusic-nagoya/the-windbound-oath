#!/usr/bin/env python3
"""Diagnostic-only CC0 basemesh renders. No sculpting, approval, or source writes."""
import argparse, hashlib, json, math, pathlib
import bpy
from mathutils import Vector

NAMES = ("GEO-body_female_stylized", "GEO-body_female_realistic")
VIEWS = {"front": (0,-1,0), "back": (0,1,0), "left": (-1,0,0), "right": (1,0,0)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    src=pathlib.Path(args.source).resolve()
    out=pathlib.Path(args.output).resolve()
    if not src.is_file() or src.is_relative_to(out) or out.is_relative_to(src):
        raise SystemExit("BLOCKED invalid paths")
    original_sha=hashlib.sha256(src.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    sources={name:bpy.data.objects.get(name) for name in NAMES}
    if any(o is None or o.type!="MESH" for o in sources.values()):
        raise SystemExit("BLOCKED named female body mesh missing")
    out.mkdir(parents=True,exist_ok=True)
    result={"status":"BLOCKED","source_sha256":original_sha,"blender":bpy.app.version_string,
            "views":[],"canonical_match":"BLOCKED","art_qa":"NOT_RUN","rig_qa":"NOT_RUN","approved":False}
    bpy.ops.object.select_all(action="SELECT")
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob,do_unlink=True)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=512
    scene.render.resolution_y=768
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.color_depth="8"
    world=bpy.data.worlds.new("QA neutral world")
    scene.world=world
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(0.12,0.12,0.12,1)
    mat=bpy.data.materials.new("QA clay material")
    mat.diffuse_color=(0.52,0.54,0.58,1)
    mat.use_nodes=True
    mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(0.52,0.54,0.58,1)
    for name,source in sources.items():
        # Reopen the immutable original before each mesh to avoid stale pointers.
        bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
        original=bpy.data.objects.get(name)
        if original is None: raise SystemExit("BLOCKED source object missing on reload")
        coords=[original.matrix_world@v.co for v in original.data.vertices]
        if not coords: raise SystemExit("BLOCKED empty mesh")
        low=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
        high=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
        size=high-low
        if min(size)<1e-5: raise SystemExit("BLOCKED degenerate bounds")
        # Remove source objects only after copying the mesh and world transform.
        mesh=original.data.copy()
        transform=original.matrix_world.copy()
        for ob in list(bpy.data.objects): bpy.data.objects.remove(ob,do_unlink=True)
        ob=bpy.data.objects.new(name+"_QA_CLAY",mesh)
        bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world=transform
        mesh.materials.clear()
        material=bpy.data.materials.new("QA_clay_"+name)
        material.diffuse_color=(0.56,0.56,0.58,1)
        ob.data.materials.append(material)
        sc=bpy.context.scene
        sc.render.engine="BLENDER_EEVEE_NEXT"
        sc.render.resolution_x=512
        sc.render.resolution_y=768
        sc.render.resolution_percentage=100
        sc.render.film_transparent=True
        sc.render.image_settings.file_format="PNG"
        sc.view_settings.view_transform="Standard"
        center=(low+high)*0.5
        # Lighting is rebuilt after each source-file reload; the first pass had no lamps.
        qa_world=bpy.data.worlds.new("QA_world_"+name)
        qa_world.use_nodes=True
        qa_world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.55,0.55,0.55,1)
        qa_world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.8
        sc.world=qa_world
        for light_name,offset,power in (
            ("key", (1.5,-2.5,2.5), 650),
            ("fill", (-2.0,-1.0,1.2), 350),
            ("rim", (0.0,2.5,2.2), 550)):
            ld=bpy.data.lights.new("QA_"+light_name,"AREA")
            ld.energy=power
            ld.shape="DISK"
            ld.size=3.0
            lo=bpy.data.objects.new("QA_"+light_name,ld)
            sc.collection.objects.link(lo)
            lo.location=center+Vector(offset)*max(size.z,1)
            lo.rotation_euler=(center-lo.location).to_track_quat("-Z","Y").to_euler()
        cam_data=bpy.data.cameras.new("QA_orthographic")
        cam=bpy.data.objects.new("QA_orthographic",cam_data)
        sc.collection.objects.link(cam)
        sc.camera=cam
        cam_data.type="ORTHO"
        # Both models share the same orthographic scale for honest side-by-side comparison.
        cam_data.ortho_scale=2.05
        center=(low+high)*0.5
        dist=max(size)*3.0
        for view,direction in VIEWS.items():
            cam.location=center+Vector(direction)*dist
            cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
            dest=out/(name+"_"+view+".png")
            sc.render.filepath=str(dest)
            bpy.ops.render.render(write_still=True)
            result["views"].append({"object":name,"view":view,"camera_ortho_scale":2.05,"file":dest.name,
                "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                "bytes":dest.stat().st_size,
                "bounds_xyz":[[round(low[i],6),round(high[i],6)] for i in range(3)]})
    result["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==original_sha
    result["status"]="PASS_DIAGNOSTIC_RENDER_ONLY" if result["source_unchanged"] and len(result["views"])==8 else "FAIL"
    (out/"diagnostic_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"render_count":len(result["views"])}))
    if result["status"]!="PASS_DIAGNOSTIC_RENDER_ONLY":raise SystemExit(2)

if __name__=="__main__":main()
