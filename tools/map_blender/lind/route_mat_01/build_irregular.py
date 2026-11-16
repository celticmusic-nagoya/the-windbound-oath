"""ROUTE-MAT-01 method B: irregular sculpted solid masonry, separate from failed box method.
Blender -b --factory-startup --python-exit-code 1 --python build_irregular.py -- --root ROOT --out OUT
"""
import argparse, hashlib, importlib.util, json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

SEED=35902
def material(root):
    path=root/"assets/candidates/route-mat-01/attempt-01/load_material.py"
    spec=importlib.util.spec_from_file_location("route_loader_b",path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.create_material(root)

def stone(name, x0,x1,z0,z1,depth, mat, rng):
    """Two irregular polygonal face rings, stitched as a genuine closed solid."""
    w=x1-x0; h=z1-z0
    # Perimeter follows irregular quadrilateral corners with intermediate edge points.
    # Offsets stay bounded to prevent accidental interpenetration and black chasms.
    outline=[(0.07,0.06),(.46,.015),(.92,.055),(.985,.31),(.955,.77),
             (.81,.96),(.43,.985),(.065,.92),(.015,.55)]
    outline=[(max(.025,min(.975,u+rng.uniform(-.045,.045))),
              max(.025,min(.975,v+rng.uniform(-.045,.045)))) for u,v in outline]
    # Front is at -depth/2, back at +depth/2, individual face relief varies.
    front=[(x0+u*w,-depth/2+rng.uniform(-.035,.035),z0+v*h) for u,v in outline]
    back=[(x0+u*w,depth/2+rng.uniform(-.025,.025),z0+v*h) for u,v in outline]
    n=len(front); verts=front+back
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+"_solid");mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name="StoneFaceUV")
    # UV face coordinates use in-bounds windows, randomized per stone.
    u0=rng.uniform(.08,.43);v0=rng.uniform(.08,.43)
    su=rng.uniform(.25,.39);sv=rng.uniform(.24,.39)
    for face in mesh.polygons:
        for li in face.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(u0+su*(v.x-x0)/w,v0+sv*(v.z-z0)/h)
    bevel=obj.modifiers.new("Chipped_Edges","BEVEL")
    bevel.width=min(w,h,depth)*rng.uniform(.025,.05)
    bevel.segments=2
    bevel.limit_method="ANGLE"
    return obj

def aim(cam,target):
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(sys.argv[sys.argv.index("--")+1:]);root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    mat,loaded=material(root)
    mortar=bpy.data.materials.new("Recessed_Lime_Mortar")
    mortar.diffuse_color=(.28,.265,.22,1)
    mortar.use_nodes=True
    mortar.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.28,.265,.22,1)
    mortar.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.91
    courses=[(.0,.35),(.35,.78),(.78,1.14),(1.14,1.57),(1.57,1.94)]
    stones=[]
    for row,(bottom,top) in enumerate(courses):
        left=-2.28+rng.uniform(-.07,.04)
        # Different coursing and variable stone width, not repeating grid cells.
        while left<2.20:
            width=min(rng.uniform(.49,1.13),2.29-left)
            if width<.20:break
            right=left+width
            # Narrow mortar gap is backed by real mortar geometry, not black void.
            gap=.018
            obj=stone("IrregularStone_%02d"%len(stones),left+gap,right-gap,
                      bottom+gap,top-gap,rng.uniform(.65,.96),mat,rng)
            stones.append(obj);left=right
    # Mortar support is deliberately slightly recessed behind the stone faces.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,.24,.97))
    backing=bpy.context.object;backing.name="FullThicknessMortarBacking"
    backing.dimensions=(4.55,.48,1.94)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    backing.data.materials.append(mortar)
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.14))
    ground=bpy.context.object;ground.name="Ground_Reference"
    ground.dimensions=(7,5,.25)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ground.data.materials.append(mortar)
    bpy.ops.object.light_add(type="AREA",location=(-3.5,-4,7))
    light=bpy.context.object;light.data.energy=900;light.data.shape="DISK";light.data.size=5
    bpy.ops.object.camera_add(location=(6,-8,5))
    cam=bpy.context.object;scene=bpy.context.scene;scene.camera=cam
    scene.render.engine="CYCLES";scene.cycles.samples=32
    scene.render.image_settings.file_format="PNG"
    views=[("overview",(6,-8,5),(0,0,1),960,720),
           ("junction-detail",(1.6,-3.6,2.3),(0,0,1.2),960,720),
           ("gameplay-distance",(9,-12,9),(0,0,1),640,480)]
    for name,pos,target,w,h in views:
        cam.location=pos;aim(cam,target);scene.render.resolution_x=w;scene.render.resolution_y=h
        scene.render.filepath=str(out/(name+".png"));bpy.ops.render.render(write_still=True)
    bpy.ops.file.pack_all()
    blend=out/"route-mat-01-irregular-candidate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report={"status":"CANDIDATE_NOT_ART_APPROVED","method":"B_irregular_polygon_solid_not_box",
            "seed":SEED,"blender":bpy.app.version_string,"stone_count":len(stones),
            "source_commit":"62f5d8d6db43e9078a71688f9c6bdee8d1d94304",
            "material_maps":loaded,"G1":"PARTIAL","G2":"NOT_RUN_INDEPENDENT",
            "G3":"PARTIAL_AUTOMATED","G4":"NOT_RUN","files":{}}
    for path in [blend]+[out/(v[0]+".png") for v in views]:
        report["files"][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/"qa.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report))

if __name__=="__main__":main()
