"""Build two depth-offset rock shoulders in the verified sunset sightline."""
from pathlib import Path

import bmesh
import bpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_windwaiting_cliff_blueprint as atlas
from build_windwaiting_headland import smooth

# X and shelf depths in provisional BU. The flank carries the lower terraces
# into the sightline gap past X=6 instead of raising the original turf lip.
STATIONS = [
    (-7.2, -4.0, -3.56, -3.15, -2.89, 3.64),  # existing tie-in
    (-4.35, -7.75, -7.31, -6.55, -4.60, 8.30),
    (-1.05, -9.10, -8.55, -7.69, -3.62, 8.83), # main scarp
    (1.0, -15.65, -14.49, -13.06, -11.29, 5.90),
    (3.35, -19.8, -19.12, -17.82, -15.23, 5.28), # shoulder A
    (4.55, -12.50, -11.88, -11.27, -9.72, 2.26),  # draw/gully
    (5.65, -13.95, -13.24, -12.38, -11.93, 3.16),
    (7.30, -24.35, -23.92, -23.09, -21.68, 4.65), # shoulder B
    (9.80, -22.70, -22.22, -21.50, -20.45, 3.30),
    (11.25, -14.60, -14.12, -13.68, -12.52, 1.37), # seaward termination
]


def section(station):
    x, toe, lower, upper, cap, top = station
    landward = smooth((x+6)/4.65)*(1-smooth((x+.20)/1.5))
    distal = smooth((x-.95)/5.5)
    # Broad intermediate landward return, then bend the two outer
    # shoulders diagonally using their distinct X/Y positions above.
    rear = -2.98+landward*1.76-distal*3.89
    # Keep the tongue narrow above tide height. Its lower root merges into
    # the coastline, while both shelf crests have open plan offsets.
    back = rear + (cap-rear)*.54*distal
    return [
        (x,toe,-.70), (x,toe-.02,.23),
        (x,lower-.39,top*.25), (x,lower-.16,top*.30), (x,lower+.62,top*.35),
        (x,upper-.23,top*.64), (x,upper+.32,top*.66),
        (x,cap-.53,top*.91), (x,cap,top),
        (x,cap+.64,top*.965),
        (x,max(cap+.77,back-.84),top*.82),
        (x,max(cap+1.02,back-.64),top*.66),
        (x,max(cap+1.16,back-.50),top*.62),
        (x,max(cap+1.38,rear-.29),top*.39),
        (x,max(cap+1.48,rear),-.70),
    ]


def prepare_rock(rock, shader):
    # UVs are world-scale along the major run of the bedding, with modest
    # compression across it. Both normal and roughness use the same chart.
    uv=rock.data.uv_layers.active
    for elt in uv.data:
        u,v=elt.uv
        elt.uv=(u+v*.105, v*1.28)
    mapping=next(node for node in shader.id_data.nodes if node.type=="NORMAL_MAP")
    mapping.inputs["Strength"].default_value=.62


def cut_seaward_brow(carrier, _probes):
    """Cut back the offshore brow with a closed wedge outside the support grid."""
    # Build a closed wedge with a ramp that returns to undisturbed terrain.
    plan=[(-10.25,-7.6,5.7),(-7.50,-7.6,3.9),(-4.40,-7.6,4.3),
          (-3.55,-7.6,5.8),(-4.25,-3.30,5.7),(-7.55,-3.24,5.25),
          (-8.78,-3.38,5.55)]
    verts=plan+[(x,y,10.0) for x,y,_ in plan]
    n=len(plan)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,j+n,i+n))
    mesh=bpy.data.meshes.new("Seaward brow cut volume")
    mesh.from_pydata(verts,[],faces)
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    cutter=bpy.data.objects.new("Seaward brow cut volume",mesh)
    bpy.context.collection.objects.link(cutter)
    old_faces=len(carrier.data.polygons)
    bpy.context.view_layer.objects.active=carrier
    mod=carrier.modifiers.new("Resection outside traversable brow","BOOLEAN")
    mod.object=cutter
    mod.operation="DIFFERENCE"
    mod.solver="EXACT"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    return {"method":"closed sloping wedge cut outside walkable shoreline",
            "wedge_floor_xyz_BU":plan,"face_count_before":old_faces,
            "face_count_after":len(carrier.data.polygons)}


if __name__=="__main__":
    atlas.main(STATIONS,section,prepare_rock,cut_seaward_brow)
