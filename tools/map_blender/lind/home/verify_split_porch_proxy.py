"""Isolated HOME portal proxy correction; exact checkpoint, no rendering or owner writes."""
import bpy, bmesh, hashlib, json, math, sys
from pathlib import Path
from mathutils import Matrix, Vector

SOURCE_SHA = "dff3a32df533c8786f3122e07cf681c18f4805bd913d750f04ce15b321b10fed"
OLD = "COL_AIDANHOUSE_porch_posts"
NAMES = ("COL_AIDANHOUSE_porch_post_west", "COL_AIDANHOUSE_porch_post_east")
PORCH = "GEO_AIDANHOUSE_PORCH"
EXPECTED = [[-1.15,-4.66,0],[1.15,-4.5,2.5]]
TARGETS = [[[-1.15,-4.707214,0],[-.83,-4.392786,2.4]],[[.83,-4.707214,0],[1.15,-4.392786,2.4]]]
RADII = (.25,.35,.45)
EPS = .0001
source, out = map(Path, sys.argv[sys.argv.index("--")+1:])
assert source.is_file() and source.resolve() != out.resolve()
assert out.is_dir()
candidate = out/"home_portal_proxy_candidate.blend"
assert not candidate.exists()

def sha(p):
    return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()

def box(points):
    pts = list(points)
    assert pts and all(math.isfinite(float(x)) for v in pts for x in v)
    return [[min(float(v[i]) for v in pts) for i in range(3)],
            [max(float(v[i]) for v in pts) for i in range(3)]]

def bounds(obj):
    assert obj.type == "MESH" and len(obj.data.vertices)
    return box(obj.matrix_world @ v.co for v in obj.data.vertices)

def close(a,b):
    return all(abs(x-y)<=EPS for p,q in zip(a,b) for x,y in zip(p,q))

def properties(obj):
    return [(k,repr(obj[k])) for k in sorted(obj.keys())]

def fingerprint(excluded):
    records = []
    for o in sorted(bpy.data.objects,key=lambda x:x.name):
        if o.name in excluded:
            continue
        row = [o.name,o.type,[list(x) for x in o.matrix_world],
               sorted(c.name for c in o.users_collection),o.hide_render,
               o.hide_viewport,properties(o)]
        if o.type == "MESH":
            m = o.data
            row += [[list(v.co) for v in m.vertices],
                    [[list(p.vertices),p.material_index,p.use_smooth] for p in m.polygons],
                    [list(e.vertices) for e in m.edges],
                    [mat.name if mat else None for mat in m.materials],
                    [[uv.name,[list(x.uv) for x in uv.data]] for uv in m.uv_layers]]
        records.append(row)
    return hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def route():
    proxies = {o.name:bounds(o) for o in bpy.data.objects
               if o.type=="MESH" and o.name.startswith("COL_AIDANHOUSE_")}
    assert proxies
    distances = []
    for i in range(123):
        x,y = 0,-5.2+i*.025
        ds = {n:math.hypot(max(a[0]-x,0,x-b[0]),max(a[1]-y,0,y-b[1]))
              for n,(a,b) in proxies.items()}
        distances.append(ds)
    return dict(samples=123,min_clearance=min(min(d.values()) for d in distances),
                radii={str(r):dict(hit_samples=sum(min(d.values())<=r for d in distances),
                      blocking_objects=sorted({n for d in distances for n,v in d.items() if v<=r}))
                       for r in RADII},proxies=proxies)

def supports():
    o=bpy.data.objects[PORCH]
    vertices=[o.matrix_world@v.co for v in o.data.vertices]
    parent=list(range(len(vertices)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    for e in o.data.edges:
        a,b=map(find,e.vertices)
        parent[a]=b
    groups={}
    for i,v in enumerate(vertices):
        groups.setdefault(find(i),[]).append(v)
    sides=[[],[]]
    for pts in groups.values():
        a,b=box(pts)
        if a[2] <= .2001 and b[2]<=2.4001 and (b[0]<-.8 or a[0]>.8):
            sides[0 if b[0]<0 else 1].append(pts)
    assert [len(s) for s in sides]==[2,2], "support component layout changed"
    return [box(v for part in side for v in part) for side in sides]

def create_proxy(name, target, old, collections):
    lo,hi=map(Vector,target)
    mesh=bpy.data.meshes.new(name+"_mesh")
    bm=bmesh.new()
    bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:
        v.co=Vector([lo[i]+(v.co[i]+.5)*(hi[i]-lo[i]) for i in range(3)])
    bm.normal_update()
    assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0
    bm.to_mesh(mesh)
    bm.free()
    obj=bpy.data.objects.new(name,mesh)
    for c in collections: c.objects.link(obj)
    for key in old.keys(): obj[key]=old[key]
    obj.hide_render=True
    obj.hide_viewport=old.hide_viewport
    obj.display_type=old.display_type
    obj.hide_set(old.hide_get())
    assert close(bounds(obj),target)
    return obj

def write(name,data):
    (out/name).write_text(json.dumps(data,indent=2)+"\n")

assert sha(source)==SOURCE_SHA
assert tuple(bpy.app.version)==(5,3,0)
assert Path(bpy.data.filepath).resolve()==source.resolve()
before=route()
write("portal-before.json",dict(source_sha256=SOURCE_SHA,route=before,scope="XY_PROXY_ONLY"))
if all(v["hit_samples"]==0 for v in before["radii"].values()):
    write("portal-result.json",dict(status="ALREADY_CLEAR_NO_EDIT",source_sha256=SOURCE_SHA,
         route=before,G1="BLOCKED",G2="NOT_RUN",G3="PARTIAL",G4="NOT_RUN"))
else:
    old=bpy.data.objects.get(OLD)
    assert old is not None and close(bounds(old),EXPECTED), "baseline proxy changed"
    assert all(v["blocking_objects"]==[OLD] for v in before["radii"].values()), "additional obstruction"
    assert not any(n in bpy.data.objects for n in NAMES)
    assert old.type=="MESH" and old.hide_render and not old.modifiers and old.parent is None
    assert len(old.data.materials)==0
    actual=supports()
    assert all(close(a,b) for a,b in zip(actual,TARGETS)), "ground supports changed"
    excluded={OLD,*NAMES}
    protected=fingerprint(excluded)
    collections=list(old.users_collection)
    assert collections and all(c.name=="COLLISION" for c in collections)
    for name,target in zip(NAMES,actual):create_proxy(name,target,old,collections)
    # Delete only the superseded box in the isolated in-memory copy.
    bpy.data.objects.remove(old,do_unlink=True)
    bpy.context.view_layer.update()
    after=route()
    assert all(v["hit_samples"]==0 for v in after["radii"].values())
    assert after["min_clearance"]>=.5799
    assert fingerprint(excluded)==protected, "non-target geometry or anchor changed"
    assert sha(source)==SOURCE_SHA
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
    saved=sha(candidate)
    bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False)
    assert sha(candidate)==saved and sha(source)==SOURCE_SHA
    assert fingerprint(excluded)==protected
    assert OLD not in bpy.data.objects
    assert all(close(bounds(bpy.data.objects[n]),a) for n,a in zip(NAMES,actual))
    assert all(bpy.data.objects[n].hide_render for n in NAMES)
    reopened=route()
    assert after==reopened
    write("portal-result.json",dict(status="ISOLATED_CORRECTION_XY_PASS",source_sha256=SOURCE_SHA,
         candidate_sha256=saved,protected_fingerprint=protected,source_unchanged=True,
         reopened=True,actual_supports=actual,before=before,after=reopened,
         G1="BLOCKED",G2="NOT_RUN",G3="PARTIAL",G4="NOT_RUN",
         scope="XY proxy only; headroom, door state, runtime not tested; candidate not adopted"))
print("HOME_PORTAL_CHECK_COMPLETE")
