"""LIND continuous cliff geology study: a SINGLE closed, nonplanar bedrock mesh.

Not a world asset. No approved scale, no phototextures or bridge edits.
Blender 4.0.2+; deterministic, candidate-only. Three clay views + .blend.
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

SEED=20261117
R=random.Random(SEED)

def fractal(x,z):
    return (0.31*math.sin(0.47*x+0.21*z)
            +0.18*math.sin(1.31*x-0.37*z)
            +0.08*math.cos(3.1*x+1.2*z)
            +0.035*math.sin(7.3*x-3.2*z))

def m(name,rgb):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*rgb,1)
    bsdf.inputs["Roughness"].default_value=0.95
    return mat

def build():
    # Cross section travels around front rock face, turf surface, rear and bottom.
    # Vertices form ONE topologically closed object, with material separation only.
    nx=113
    front_n=45
    top_n=19
    back_n=17
    bottom_n=19
    ring_n=front_n+top_n+back_n+bottom_n
    verts=[]
    faces=[]
    mids=[]
    for i in range(nx):
        x=-12+24*i/(nx-1)
        crest=7.1+0.38*math.sin(0.42*x)+0.21*math.sin(1.07*x)
        foot=0.16*math.sin(0.3*x)
        profile=[]
        for j in range(front_n):
            t=j/front_n
            z=foot+(crest-foot)*t
            # Differential erosion: overhang near crest, concave base, varied
            # stratification and localized scarps. No Voronoi extrusion.
            undercut=-0.47*math.exp(-((t-0.10)/0.12)**2)
            overhang=0.64*math.exp(-((t-0.87)/0.14)**2)
            band=0.16*math.sin(11*t+0.7*x)+0.09*math.sin(27*t-0.23*x)
            y=0.2+undercut+overhang+band+fractal(x,z)*(0.35+0.5*t)
            # Crevices cut into rock face along tilted, discontinuous traces.
            for phase in (-5.4,1.3,7.1):
                trace=x-phase-1.2*math.sin(0.43*z+phase)
                depth=0.32*math.exp(-(trace/0.19)**2)
                y-=depth*(0.4+0.6*math.sin(0.6*z+phase)**2)
            profile.append((x,y,z))
        for j in range(top_n):
            t=j/top_n
            y=0.7-8.7*t
            z=crest+0.22*math.sin(0.55*x+0.8*y)+0.10*math.cos(1.8*x-0.4*y)
            profile.append((x,y,z))
        for j in range(back_n):
            t=j/back_n
            z=crest*(1-t)+(-1.7)*t
            profile.append((x,-8.0,z))
        for j in range(bottom_n):
            t=j/bottom_n
            y=-8+8.2*t
            profile.append((x,y,-1.7))
        assert len(profile)==ring_n
        verts.extend(profile)
    for i in range(nx-1):
        for j in range(ring_n):
            k=i*ring_n+j
            jn=(j+1)%ring_n
            faces.append((k,i*ring_n+jn,(i+1)*ring_n+jn,k+ring_n))
            mids.append(1 if front_n<=j<front_n+top_n else 0)
    faces.append(tuple(reversed(range(ring_n))))
    mids.append(0)
    faces.append(tuple((nx-1)*ring_n+j for j in range(ring_n)))
    mids.append(0)
    mesh=bpy.data.meshes.new("continuous_cliff_bedrock_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob=bpy.data.objects.new("GEO_CONTINUOUS_CLIFF_CANDIDATE",mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m("CLAY_BEDROCK",(0.46,0.44,0.42)))
    ob.data.materials.append(m("CLAY_SOIL_TOP",(0.61,0.59,0.53)))
    for p,mi in zip(mesh.polygons,mids):
        p.material_index=mi
        p.use_smooth=True
    # Planarity and topological closure QA: every mesh edge has two faces.
    incidence={}
    for poly in mesh.polygons:
        for ek in poly.edge_keys:
            key=tuple(sorted(ek))
            incidence[key]=incidence.get(key,0)+1
    bad=sum(v!=2 for v in incidence.values())
    return ob,{"vertices":len(verts),"faces":len(faces),"boundary_or_nonmanifold_edges":bad}

def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name)
    ob=bpy.data.objects.new(name,d)
    bpy.context.collection.objects.link(ob)
    ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
    d.type="ORTHO"
    d.ortho_scale=scale
    return ob

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    a=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    out=Path(a.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    ob,geometry=build()
    assert geometry["boundary_or_nonmanifold_edges"]==0,geometry
    bpy.ops.object.light_add(type="AREA",location=(-5,10,16))
    light=bpy.context.object
    light.data.energy=2400
    light.data.shape="DISK"
    light.data.size=12
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
    scene.render.resolution_x=1100
    scene.render.resolution_y=750
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.world.color=(0.30,0.30,0.30)
    views={
      "front":((0,19,8),(0,-1,3.1),28),
      "oblique":((16,15,12),(0,-1,3.3),30),
      "top_contact":((2,12,25),(0,-3,5),29),
    }
    renders={}
    for name,(loc,target,scale) in views.items():
        scene.camera=camera("QA_CAM_"+name,loc,target,scale)
        p=out/(name+".png")
        scene.render.filepath=str(p)
        bpy.ops.render.render(write_still=True)
        renders[name]={"path":p.name,"sha256":digest(p)}
    blend=out/"continuous_cliff_study.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report={
      "status":"CANDIDATE_NOT_ART_APPROVED",
      "method":"single_continuous_closed_rock_mesh_with_nonplanar_erosion",
      "seed":SEED,
      "geometry":geometry,
      "blender_version":bpy.app.version_string,
      "source_image_sha256":"abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620",
      "source_usage":"reference only; no direct geometry alignment asserted",
      "blend_sha256":digest(blend),
      "renders":renders,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"LIMITED_TECH_QA","G4":"NOT_RUN",
      "limits":["procedural clay study; not photo-scanned Irish cliff",
                "no approved real-world scale or spatial placement",
                "no navigation, collision, game-size QA or textures"]
    }
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("CONTINUOUS_CLIFF_COMPLETE",json.dumps(geometry))

if __name__=="__main__":
    main()
