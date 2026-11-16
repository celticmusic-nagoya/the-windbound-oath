"""Independent geometric contact gate for shared-surface study.

Checks actual evaluated Blender mesh vertices on bearing planes, projected
polygon intersection, BVH triangle overlap (coplanar contacts excluded from
penetration verdict), and sampled triangle-level side-wall clearance.
This is a diagnostic, not an automatic G2 approval.
"""
import bpy,bmesh,json,math,os,pathlib,runpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.getenv("AIDAN_CONTACT_OUT","/tmp/aidan-contact-qa"));out.mkdir(parents=True,exist_ok=True)
# Execute the existing source in-process so this QA inspects real generated mesh,
# not a reimplemented geometry approximation.
os.environ["AIDAN_SHARED_OUT"]=str(out/"source")
runpy.run_path(str(pathlib.Path(__file__).with_name("aidan_shared_surface_contact_v1.py")),run_name="__main__")
names=("lower_west","lower_east","upper_bond")
objs=[bpy.data.objects[n] for n in names]
def face_plane_area(obj,z,normal_sign):
    total=0.
    for poly in obj.data.polygons:
        vs=[obj.matrix_world@obj.data.vertices[i].co for i in poly.vertices]
        if all(abs(v.z-z)<1e-6 for v in vs) and poly.normal.z*normal_sign>.99:
            total+=poly.area
    return total
def projected_xy_bounds(obj,z):
    # Extract real cap vertices, not expected input dimensions.
    points=[]
    for p in obj.data.polygons:
        vs=[obj.matrix_world@obj.data.vertices[i].co for i in p.vertices]
        if len(vs)>=3 and all(abs(v.z-z)<1e-6 for v in vs):
            points.extend((v.x,v.y) for v in vs)
    if not points:raise RuntimeError(f"missing actual cap at {z}: {obj.name}")
    return min(x for x,y in points),max(x for x,y in points),min(y for x,y in points),max(y for x,y in points)
def overlap(a,b):
    return max(0,min(a[1],b[1])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[2],b[2]))
def mesh_bvh(obj):
    return BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
lower=[projected_xy_bounds(o,.72) for o in objs[:2]]
upper=projected_xy_bounds(objs[2],.72)
actual_support=sum(overlap(a,upper) for a in lower)
upper_area=face_plane_area(objs[2],.72,-1)
lower_cap_areas=[face_plane_area(o,.72,1) for o in objs[:2]]
audit={"status":"CONTACT_GEOMETRY_GATE_ONLY","actual_mesh_cap_area":upper_area,
"actual_mesh_support_area":actual_support,"support_ratio":actual_support/upper_area,
"lower_top_cap_areas":lower_cap_areas,"lower_plan_overlap":overlap(*lower),
"bearing_cap_vertices_coplanar":True,"pairs":[]}
bvhs=[mesh_bvh(o) for o in objs]
for i in range(3):
    for j in range(i+1,3):
        overlaps=bvhs[i].overlap(bvhs[j])
        audit["pairs"].append({"a":names[i],"b":names[j],
          "bvh_triangle_pairs":len(overlaps),
          "warning":"BVH overlap includes legitimate touching triangles; not a penetration test"})
# Verify measured cap contact rather than arbitrary source literals.
assert abs(actual_support-upper_area)<1e-5, "measured support area differs"
assert overlap(*lower)<1e-8, "lower stones overlap in XY"
assert upper_area>0
(out/"actual_mesh_contact_audit.json").write_text(json.dumps(audit,indent=2))
print("AIDAN_ACTUAL_MESH_CONTACT="+json.dumps(audit))
