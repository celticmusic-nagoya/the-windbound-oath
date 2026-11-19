"""Import actual CC0 Poly Haven coastal cliff glTF in headless Blender.

Four orthographic studio views: front, oblique, reverse, top; plus a PBR
hero view from publisher textures. No synthetic geology substitutions.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

import bpy

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def view(scene,name,pos,target,width,out,engine="BLENDER_WORKBENCH"):
    cam=bpy.data.cameras.new("SCAN_QA_"+name)
    obj=bpy.data.objects.new("SCAN_QA_"+name,cam)
    bpy.context.collection.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    cam.type="ORTHO"
    cam.ortho_scale=width
    cam.clip_end=10000
    scene.camera=obj
    scene.render.engine=engine
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)
    path=out/(name+".png")
    return {"path":path.name,"sha256":sha(path),"engine":engine}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",required=True)
    a.add_argument("--asset",default="coastal_cliff_04")
    args=a.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    out=Path(args.out).resolve()
    manifest=json.loads((out/"source_manifest.json").read_text())
    assert manifest["asset_id"]==args.asset
    original=out/"sources"/args.asset/(args.asset+"_1k.gltf")
    assert original.exists()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(original))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes: raise RuntimeError("No mesh imported")
    coords=[]
    from mathutils import Vector
    for obj in meshes:
        for bound in obj.bound_box:
            coords.append(obj.matrix_world @ Vector(bound))
    minimum=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    maximum=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    size=maximum-minimum
    center=(minimum+maximum)*0.5
    tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    uv=sum(len(o.data.uv_layers) for o in meshes)
    if tri<100000 or uv==0:
        raise RuntimeError("Scan geometry or UV missing")
    width_axis=0 if size.x>=size.y else 1
    depth_axis=1-width_axis
    def p(w,d,h):
        v=center.copy()
        v[width_axis]+=w
        v[depth_axis]+=d
        v[2]+=h
        return v
    span=max(size.x,size.y)
    height=size.z
    dist=span*1.9
    target=p(0,0,0)
    scene=bpy.context.scene
    scene.render.resolution_x=1024
    scene.render.resolution_y=720
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type="BOTH"
    # Groundless studio views intentionally expose original source cut edges.
    views={
        "front":(p(0,dist,height*0.8),max(span*1.2,height*2.0)),
        "oblique":(p(dist*0.62,dist,height*1.3),span*1.45),
        "reverse":(p(0,-dist,height*0.8),max(span*1.2,height*2.0)),
        "top":(p(0,span*0.1,dist),span*1.25)
    }
    renders={}
    for name,(pos,scale) in views.items():
        renders[name]=view(scene,name,pos,target,scale,out)
    # PBR preview directly from imported publisher material, without photo retouching.
    world=bpy.data.worlds.new("SCAN_QA_WORLD") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world=world
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value=(0.48,0.50,0.53,1)
        bg.inputs["Strength"].default_value=0.7
    light_data=bpy.data.lights.new("SCAN_QA_KEY",type="AREA")
    light=bpy.data.objects.new("SCAN_QA_KEY",light_data)
    bpy.context.collection.objects.link(light)
    light.location=p(-span*0.3,span*0.6,span*0.6)
    light_data.energy=7000
    light_data.size=span*0.7
    light.rotation_euler=(target-light.location).to_track_quat("-Z","Y").to_euler()
    engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
    if hasattr(scene,"eevee"):
        scene.eevee.taa_render_samples=16
    renders["pbr_oblique"]=view(scene,"pbr_oblique",views["oblique"][0],target,views["oblique"][1],out,engine)
    for o in meshes:
        o["scan_candidate_only"]=True
    # Pack original 1K textures so the saved .blend can reopen independently.
    bpy.ops.file.pack_all()
    blend=out/"coastal_cliff_scan_study.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report={
       "asset_id":args.asset,
       "source":"Poly Haven glTF original 1K textures + original source mesh",
       "status":"CANDIDATE_NOT_APPROVED",
       "geometry":{"mesh_objects":len(meshes),"triangles":tri,"uv_layer_count":uv,
                   "bounding_box_min":list(minimum),"bounding_box_max":list(maximum),
                   "bounding_box_extents":list(size)},
       "blender_version":bpy.app.version_string,
       "original_scan_unchanged":True,
       "blender_blend":{"path":blend.name,"sha256":sha(blend)},
       "renders":renders,
       "G1":"SOURCE_RIGHTS_PASS_SPATIAL_BLOCKED",
       "G2":"NOT_RUN","G3":"PARTIAL_TECH_CHECK","G4":"NOT_RUN",
       "notes":["no accepted LIND-world transform or Irish provenance",
                "camera directions are diagnostic, not accepted production framing",
                "original source geometry not altered; material rendered directly"]
    }
    (out/"render_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SCAN_3D_COMPLETE",json.dumps(report["geometry"]))
if __name__=="__main__":
    main()
