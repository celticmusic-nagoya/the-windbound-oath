"""LIND CLIFF-JOINT-01: independent, irregular joint-cell cliff study.

Candidate only. This is a *local geological study module*, not a full world,
bridge or accepted Irish geology. No existing assets are overwritten.
Run with Blender: blender -b --factory-startup --python-exit-code 1 --python
tools/map_blender/lind/build_jointed_cliff_study.py -- --out /tmp/lind-joint-study
"""
import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SEED = 20261117
def clip(poly, nx, nz, limit):
    if not poly:
        return []
    out = []
    prev = poly[-1]
    dp = nx * prev[0] + nz * prev[1] - limit
    for curr in poly:
        dc = nx * curr[0] + nz * curr[1] - limit
        if (dp <= 0) != (dc <= 0):
            t = dp / (dp - dc)
            out.append((prev[0] + t * (curr[0] - prev[0]), prev[1] + t * (curr[1] - prev[1])))
        if dc <= 0:
            out.append(curr)
        prev, dp = curr, dc
    return out

def make_cell(i, poly, rng, mat):
    # X/Z polygon: irregular fracture-bounded outcrop, not rectangular masonry.
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    # Negative Y is inward rock mass. Every cell shares a buried rear surface.
    depth = rng.uniform(0.12, 0.62)
    vertices = []
    for x, z in poly:
        erosion = 0.10 * math.sin(1.7 * x + 2.3 * z) + 0.06 * math.cos(3.1 * x - z)
        vertices.append((x, depth + erosion, z))
    for x, z in poly:
        vertices.append((x, -0.95, z))
    n = len(poly)
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    faces += [(j, (j+1)%n, (j+1)%n+n, j+n) for j in range(n)]
    mesh = bpy.data.meshes.new("fracture_cell_mesh_%02d" % i)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("GEO_JOINT_%02d" % i, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def make_terrain(rng, mat):
    # Continuous grass-topped land mass, not a repeating stack of blocks.
    nx, ny = 25, 15
    verts = []
    for j in range(ny):
        y = -9.0 + j * 0.65
        for i in range(nx):
            x = -10.0 + i * (20.0/(nx-1))
            z = 5.75 + 0.25*math.sin(0.6*x) + 0.14*math.sin(1.3*x+0.5*y)
            z += 0.16*math.sin(0.7*y) + 0.06*math.sin(2.7*x+1.4*y)
            verts.append((x,y,z))
    faces = []
    for j in range(ny-1):
        for i in range(nx-1):
            a = j*nx+i
            faces.append((a,a+1,a+1+nx,a+nx))
    mesh=bpy.data.meshes.new("continuous_turf_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob=bpy.data.objects.new("GEO_TURF_TOP_CANDIDATE",mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)

def material(name, rgb, rough=1):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1)
    mat.use_nodes=True
    p=mat.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*rgb,1)
    p.inputs["Roughness"].default_value=rough
    return mat

def point_camera(name, loc, target, ortho):
    cam=bpy.data.cameras.new(name)
    obj=bpy.data.objects.new(name,cam)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    cam.type="ORTHO"
    cam.ortho_scale=ortho
    return obj

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    out=Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    cliff=bpy.data.collections.new("LIND_GEO_JOINTED_CLIFF_STUDY")
    bpy.context.scene.collection.children.link(cliff)
    # Active collection for generated geometry
    bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[cliff.name]
    rock=material("CLAY_ROCK_NO_PBR",(0.46,0.43,0.40))
    turf=material("CLAY_TURF_NO_PBR",(0.59,0.59,0.55))
    sites=[]
    for _ in range(44):
        sites.append((rng.uniform(-9.3,9.3),rng.uniform(0.4,5.4)))
    domain=[(-10,0),(10,0),(10,5.8),(-10,5.8)]
    count=0
    for i,(x,z) in enumerate(sites):
        poly=list(domain)
        for j,(xx,zz) in enumerate(sites):
            if i==j:
                continue
            # Voronoi half-plane: squared-distance comparison
            nx,nz=xx-x,zz-z
            limit=(xx*xx+zz*zz-x*x-z*z)/2
            poly=clip(poly,nx,nz,limit)
            if len(poly)<3:
                break
        if len(poly)>=3:
            # Preserve irregular natural joint silhouettes; avoid periodic bricks.
            make_cell(i,poly,rng,rock)
            count+=1
    make_terrain(rng,turf)
    world=bpy.context.scene.world
    world.color=(0.28,0.28,0.28)
    bpy.ops.object.light_add(type="AREA",location=(-5,8,12))
    light=bpy.context.object
    light.name="STUDY_SOFTBOX"
    light.data.energy=1900
    light.data.shape="DISK"
    light.data.size=11
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
    scene.render.resolution_x=1000
    scene.render.resolution_y=700
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    views={
      "front":((0,17,8),(0,0,3),22),
      "three_quarter":((15,14,12),(0,0,3),24),
      "top_contact":((2,8,21),(0,-2,4),24),
    }
    renders={}
    for name,(loc,target,scale) in views.items():
        scene.camera=point_camera("STUDY_CAMERA_"+name,loc,target,scale)
        path=out/(name+".png")
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        renders[name]={"path":path.name,"sha256":sha(path)}
    blend=out/"jointed_cliff_study.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report={
      "asset_status":"candidate",
      "method_family":"irregular_voronoi_fracture_cell_cliff_study",
      "seed":SEED,
      "blender_version":bpy.app.version_string,
      "joint_cells":count,
      "source_world_sha256":"abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620",
      "source_usage":"reference only; source not imported",
      "model_sha256":sha(blend),
      "renders":renders,
      "G1":"BLOCKED",
      "G2":"NOT_RUN",
      "G3":"RENDERED_NOT_INDEPENDENTLY_QA",
      "G4":"NOT_RUN",
      "warnings":["Geological study only, not approved Irish geology","Turf contact and full support not independently tested","No textures, UV, navmesh, collisions or Android QA"]
    }
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("CLIFF_STUDY_DONE",json.dumps({"joint_cells":count,"outputs":list(renders)}))

if __name__=="__main__":
    main()
