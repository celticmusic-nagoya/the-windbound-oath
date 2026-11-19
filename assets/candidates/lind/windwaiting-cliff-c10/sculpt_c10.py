"""C10 experimental independent rock masses. Blender 5.3.0 candidate runtime.
Input: C9-B/C_UNAPPROVED.blend. No mutation of source or C9 files.
This stage creates editable, closed, independently authored cliff blocks;
it does NOT certify visual fit, intersections, or seam preservation.
"""
import argparse
import math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

# Distinctive nonperiodic masses: center X, base Z, top Z, half-width,
# outward thickness, back inset, inclined break (X/Z).
MASSES = (
    (-10.9, .55, 5.6, 1.30, .91, .24, -.23),
    (-7.8, .75, 6.1, 1.06, 1.20, .29, .31),
    (-5.0, .45, 5.0, 1.46, .83, .18, -.35),
    (-2.0, .68, 3.85, 1.08, .66, .20, .28),
)
# Authored fractured silhouette, not repeated cubes or a heightfield.
OUTLINE = ((-.94,.08),(-.72,.02),(-.42,.12),(-.14,.0),
           (.21,.09),(.58,.0),(.96,.13),(1.,.39),
           (.82,.57),(.93,.80),(.65,.98),(.24,.92),
           (-.11,1.),(-.39,.88),(-.76,.96),(-.91,.69),(-1.,.43))

def carrier():
    matches=[o for o in bpy.data.objects if o.type=="MESH" and o.get("variant")=="B"]
    if len(matches)!=1:
        raise RuntimeError("Expected exactly one C9 B carrier mesh")
    return matches[0]

def make_locator(obj):
    # Use world-space nearest (X,Z) vertex; reject remote projections.
    world=[obj.matrix_world @ v.co for v in obj.data.vertices]
    kd=KDTree(len(world))
    for i,v in enumerate(world):
        kd.insert((v.x,0,v.z),i)
    kd.balance()
    def locate(x,z):
        _,idx,dist=kd.find((x,0,z))
        if dist>1.25:
            raise ValueError(f"Unsupported carrier projection: {x:.2f},{z:.2f} ({dist:.2f})")
        return world[idx].y
    return locate

def build_mass(collection, name, spec, locate):
    cx,low,high,half,projection,inset,rake=spec
    coords=[]
    n=len(OUTLINE)
    for side in (0,1):
        for i,(u,v) in enumerate(OUTLINE):
            z=low+(high-low)*v
            x=cx+half*u+rake*(z-(low+high)*.5)
            y0=locate(x,z)
            # Depth variation is tied to the rock's independent facets.
            facet=.10*math.sin(i*2.17+cx)+.07*math.cos(i*.89)
            y=y0+(inset if side else -projection+facet)
            coords.append((x,y,z))
    faces=[]
    # Reverse front winding relative to rear; validate after actual Blender run.
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(range(n,2*n)))
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    mesh=bpy.data.meshes.new(name+" mesh")
    mesh.from_pydata(coords,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj["status"]="UNAPPROVED_C10_GEOMETRY_STUDY"
    obj["construction"]="independent closed fracture mass"
    obj["source"]="C9 B carrier world-space projection"
    return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    if tuple(bpy.app.version)!=(5,3,0):
        raise RuntimeError("Blender 5.3.0 required")
    if not args.source.is_file():
        raise FileNotFoundError(args.source)
    args.output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
    obj=carrier()
    locate=make_locator(obj)
    collection=bpy.data.collections.new("C10 | Independent large fractured masses | UNAPPROVED")
    bpy.context.scene.collection.children.link(collection)
    material=obj.data.materials[0] if obj.data.materials else None
    for i,spec in enumerate(MASSES):
        mass=build_mass(collection,f"C10 large rock {i+1:02d}",spec,locate)
        if material:
            mass.data.materials.append(material)
    bpy.context.scene["candidate"]="C10_UNAPPROVED"
    bpy.context.scene["c10_stage"]="geometry construction; render and QA NOT_RUN"
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/"windwaiting_cliff_C10_UNAPPROVED.blend").resolve()),compress=True)
    print("C10 saved; no render or QA claim",flush=True)

if __name__=="__main__":
    main()
