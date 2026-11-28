"""V52 isolated read-only native interface and virtual rock-placement feasibility.
No save or edits of the source scene; candidate translations evaluated on numerical copies.
Run only on exact V21 archive with Blender 5.3.0. No D4 or adoption claim."""
import bpy,sys,math,hashlib,json,struct
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import convex_hull_2d
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='69789159a2f0502706fb0d1bc0e9f3a62fdb68dfea852fc81ee2b0d7ee86ce05'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
oo=[o for o in scene.objects if o.type=='MESH']
for o in oo:o.data.calc_loop_triangles()
assert len(oo)==479 and sum(len(o.data.loop_triangles) for o in oo)==926746
assert not [i for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
def geom(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return (h.hexdigest(),tuple(tuple(r) for r in o.matrix_world))
protected={o.name:geom(o) for o in oo}
terrain=bpy.data.objects['A3 provisional reconstructed terrain']
inv=terrain.matrix_world.inverted()
def hit(x,y):
    a=inv@Vector((x,y,100));direction=inv.to_3x3()@Vector((0,0,-1))
    ok,p,n,i=terrain.ray_cast(a,direction,distance=200)
    assert ok,(x,y)
    return (terrain.matrix_world@p).z
def footprint(o,root=False):
    xyz=[o.matrix_world@v.co for v in o.data.vertices]
    bottom=min(v.z for v in xyz)
    xy=[Vector((v.x,v.y)) for v in xyz if not root or v.z<=bottom+1.2]
    pts=[xy[i] for i in convex_hull_2d(xy)]
    assert len(pts)>=3,o.name
    return pts
def ps(p,a,b):
    v=b-a;d=v.length_squared
    return (p-a-v*max(0,min(1,(p-a).dot(v)/d))).length if d>1e-18 else (p-a).length
def cross(a,b):return a.x*b.y-a.y*b.x
def inside(p,h):
    v=[cross(b-a,p-a) for a,b in edges(h)]
    return min(v)>=-1e-8 or max(v)<=1e-8
def edges(h):return zip(h,h[1:]+h[:1])
def seg(a,b,c,d):
    x=cross(b-a,c-a);y=cross(b-a,d-a);u=cross(d-c,a-c);v=cross(d-c,b-c)
    if x*y<0 and u*v<0:return 0.
    return min(ps(a,c,d),ps(b,c,d),ps(c,a,b),ps(d,a,b))
def pointpoly(p,h):return 0. if inside(p,h) else min(ps(p,a,b) for a,b in edges(h))
def linepoly(a,b,h):
    if inside(a,h) or inside(b,h):return 0.
    return min(seg(a,b,c,d) for c,d in edges(h))
def poly_gap(a,b):
    if inside(a[0],b) or inside(b[0],a):return 0.
    return min(seg(p,q,r,s) for p,q in edges(a) for r,s in edges(b))
def bbox(h):return (min(p.x for p in h),max(p.x for p in h),min(p.y for p in h),max(p.y for p in h))
def bboxgap(a,b):return math.hypot(max(0,a[0]-b[1],b[0]-a[1]),max(0,a[2]-b[3],b[2]-a[3]))
route=(Vector((-205,140)),Vector((90,-90)))
reserved=[((67.536852,-72.486359),11),((45.876293,-75.886764),8),((49.408698,-58.352544),10),((93.943160,-93.074328),7)]
rays=[((65.4663,-80.2138),(45.876293,-75.886764),4),((65.4663,-80.2138),(93.943160,-93.074328),3)]
def reserved_gap(h):
    return min([linepoly(*route,h)-5]+[pointpoly(Vector(c),h)-r for c,r in reserved]+[linepoly(Vector(a),Vector(b),h)-r for a,b,r in rays])

# V51 actual GLB boundary Z values, SHA-verified local inspection V52.
zs=[26.698108673095703,26.75173568725586,26.801937103271484,26.848554611206055,26.891437530517578,26.93043327331543,26.965396881103516,26.99618911743164,27.022672653198242,27.044723510742188,27.062219619750977,27.075050354003906,27.083110809326172,27.086305618286133,27.084556579589844,27.077787399291992,27.06593894958496,27.048961639404297,27.026819229125977,26.99948501586914,26.966949462890625]
boundary={round(v.y,5):float(v.z) for v in (terrain.matrix_world@v.co for v in terrain.data.vertices) if abs(v.x+100)<1e-6 and -50.000001<=v.y<=0.000001}
assert len(boundary)==21
deltas=[boundary[-50+2.5*i]-z for i,z in enumerate(zs)]
# Evaluate actual native geometry in numerical virtual work copy; no object mutation.
targets={
 'V21_R_002':((6.6,-17.36,35.12),-0.21348104145198743,(0.22247967345311057,0.1616409443804301,-0.000006120060319858567)),
 'V21_R_008':((39.7,-43.17,29.99),-0.14331462754618673,(0.1576021507213444,0.12313229506513167,-0.000002806812226197053)),
 'V21_R_011':((58.1,-53.71,28.02),-1.2648504665445959,(1.2285186073009933,0.4963537362760834,-0.01979657747185115))}
obs={}
for o in oo:
    if o==terrain:continue
    h=footprint(o,o.name.startswith(('V18_T_','V18_D_','V19_BG_')))
    obs[o.name]=h
rows=[]
for name,(loc,oldgap,delta) in targets.items():
    o=bpy.data.objects[name]
    assert (o.location-Vector(loc)).length<1e-4
    h=obs[name];g=reserved_gap(h);assert abs(g-oldgap)<1e-4,(name,g,oldgap)
    obs[name]=[p+Vector(delta[:2]) for p in h]
for name,(loc,oldgap,delta) in targets.items():
    o=bpy.data.objects[name];h=obs[name];bb=bbox(h)
    best=1000.;nearest=None
    for n,k in obs.items():
        if n==name or bboxgap(bb,bbox(k))>best:continue
        d=poly_gap(h,k)
        if d<best:best=d;nearest=n
    xyz=[o.matrix_world@v.co for v in o.data.vertices];bottom=min(v.z for v in xyz)
    root=[v+Vector(delta) for v in xyz if v.z<=bottom+.12]
    residual=[v.z-hit(v.x,v.y) for v in root]
    g=reserved_gap(h)
    passed=g>=.045 and best>=.045 and min(residual)>=-.20 and min(abs(x) for x in residual)<=.05
    rows.append(dict(name=name,old_protected_gap_m=oldgap,virtual_translation_m=delta,actual_native_virtual_protected_gap_m=g,actual_native_virtual_obstacle_gap_m=best,nearest_obstacle=nearest,root_min_m=min(residual),root_nearest_abs_m=min(abs(x) for x in residual),screen_pass=passed))
assert all(geom(o)==protected[o.name] for o in oo) and sha(src)==lock
q=dict(status='NATIVE_VIRTUAL_SCREEN_PASS' if all(r['screen_pass'] for r in rows) and max(map(abs,deltas))<=1e-6 else 'HOLD',source_sha256=lock,blender=bpy.app.version_string,protected_meshes_exact=len(protected),seam_samples=21,max_seam_delta_m=max(map(abs,deltas)),seam_deltas_m=deltas,virtual_placement_rows=rows,limits=['No native mutation or save; actual V51 GLB boundary values from prior SHA-verified local survey, not runtime navigation. V47B route, C03 receiver, independent D4/G2 and G4 remain HOLD. Provisional numerical screens, not accepted tolerances.'])
(out/'v52_native_virtual_qa.json').write_text(json.dumps(q,indent=2)+'\n')
print(q)
