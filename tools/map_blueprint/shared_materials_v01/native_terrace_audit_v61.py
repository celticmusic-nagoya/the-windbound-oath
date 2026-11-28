"""Read-only V61 native interface survey, not D4 or placement acceptance."""
import bpy,sys,math,hashlib,json
from pathlib import Path
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='24bd47906a6ce456441147021929d543ee700624fc6779fc7e251133a196298a'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene;old=[o for o in scene.objects if o.type=='MESH'];assert len(old)==523
terrain=bpy.data.objects['A3 provisional reconstructed terrain'];inv=terrain.matrix_world.inverted()
origin=(93.9431596631828,-93.0743278729908)
nx,ny=-.6148655745981655,-.788631932636555
dx,dy=.788631932636555,-.6148655745981655
def local(v):
    a,b=v.x-origin[0],v.y-origin[1]
    return (a*nx+b*ny,a*dx+b*dy,v.z)
def ground(x,y):
    a,b=origin[0]+nx*x+dx*y,origin[1]+ny*x+dy*y
    ok,p,n,i=terrain.ray_cast(inv@Vector((a,b,100)),inv.to_3x3()@Vector((0,0,-1)),distance=200)
    assert ok,(x,y)
    return (terrain.matrix_world@p).z
# compare native terrain against exact source TIN design at pad corners and all approach vertices.
ramp=[[-1.5,-10,27.728204203008566],[-1.5,-4,28.34],[.7282584552,-10,27.870255930095922],[.7282584552,-4,28.34],[1.5,-10,27.918704630888406],[1.5,-4,28.34]]
pad_samples=[ground(i/4,j/4) for i in range(-16,17) for j in range(-16,17)]
seam=[abs(ground(x,y)-z) for x,y,z in ramp if y==-10]
# Exact polygon clipping of native triangle against conservative rectangular 3D study volumes.
# Volume includes floor/support plus 2m clearance above interaction deck. It is NOT a runtime capsule.
vols={'pad':((-4,4),(-4,4),(27.55,30.88)), 'approach':((-1.5,1.5),(-10,-4),(27.55,30.34))}
def clip(poly,axis,k,sign):
    if not poly:return []
    result=[];a=poly[-1];fa=sign*(a[axis]-k)
    for b in poly:
        fb=sign*(b[axis]-k)
        if (fa>=0)!=(fb>=0):
            t=fa/(fa-fb);result.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(3)))
        if fb>=0:result.append(b)
        a,fa=b,fb
    return result
def test(a,vol):
    for i,(lo,hi) in enumerate(vol):
        a=clip(a,i,lo,1);a=clip(a,i,hi,-1)
        if not a:return False
    return len(a)>=3
def broad(v,vol):
    return all(max(p[i] for p in v)>=lo and min(p[i] for p in v)<=hi for i,(lo,hi) in enumerate(vol))
hits=[];checked=0
for o in old:
    if o==terrain or o.name=='V58_SCENIC_ONLY_terrain_extension':continue
    bb=[local(o.matrix_world@Vector(v)) for v in o.bound_box]
    vs={n:b for n,b in vols.items() if broad(bb,b)}
    if not vs:continue
    checked+=1
    v=[local(o.matrix_world@p.co) for p in o.data.vertices];o.data.calc_loop_triangles()
    count={n:0 for n in vs}
    for tri in o.data.loop_triangles:
        a=[v[i] for i in tri.vertices]
        for n,vol in vs.items():
            if broad(a,vol) and test(a,vol):count[n]+=1
    if any(count.values()):hits.append(dict(name=o.name,counts=count,replaceable_old_proxy=o.name.startswith(('V57_ALTAR_PROXY_','V57_ARCH_PROXY_'))))
assert sha(src)==lock
q=dict(status='READ_ONLY_NATIVE_INTERFACE_SURVEY',source_sha256=lock,blender=bpy.app.version_string,mesh_count=len(old),candidate_objects_checked=checked,pad_sample_count=len(pad_samples),pad_sample_ground_range_m=[min(pad_samples),max(pad_samples)],min_platform_clearance_m=28.34-max(pad_samples),approach_seam_residuals_m=seam,volume_hits=hits,unexpected_volume_hits=[a for a in hits if not a['replaceable_old_proxy']],limits=['Conservative boxes, not exact player collision. Intended original terrain excluded; old altar/arch proxies are reported separately, never removed. No source save, no native geometry created.','Final V47B and adjacent terrain unavailable; actual navigation/trigger and D4 not certified.'])
(out/'v61_native_audit.json').write_text(json.dumps(q,indent=2)+'\n');print(q)
