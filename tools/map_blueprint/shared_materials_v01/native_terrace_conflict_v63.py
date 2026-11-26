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
# Classify the exact prior hit and subvolumes. No native mutations.
o=bpy.data.objects['V58_SCENIC_GROVE_00']
vs=[local(o.matrix_world@p.co) for p in o.data.vertices]
o.data.calc_loop_triangles()
def cut(p,vol):
    for i,(lo,hi) in enumerate(vol):
        p=clip(p,i,lo,1);p=clip(p,i,hi,-1)
        if not p:return []
    return p
vols={'old_pad':((-4,4),(-4,4),(27.55,30.88)),
      'foundation_envelope':((-4,4),(-4,4),(27.55,28.29)),
      'cap':((-4,4),(-4,4),(28.29,28.34)),
      'interaction':((-1.15,1.15),(-1.4,.1),(28.88,30.88)),
      'access_on_pad':((-1.5,1.5),(-4,-2.6),(28.34,30.34)),
      'access_ramp_envelope':((-1.5,1.5),(-10,-4),(27.55,30.34)),
      'altar_assembly_envelope':((-3.26,3.26),(-2.6,3.28),(28.34,31.86)),
      'pad_above_walk':((-4,4),(-4,4),(28.34,30.88))}
def area3(p):
    if len(p)<3:return 0.
    v=[Vector(x) for x in p]
    return sum((v[i]-v[0]).cross(v[i+1]-v[0]).length*.5 for i in range(1,len(v)-1))
rows=[]
for tri in o.data.loop_triangles:
    a=[vs[i] for i in tri.vertices]
    hits={}
    for n,v in vols.items():
        if not broad(a,v):continue
        p=cut(a,v)
        if len(p)>=3:hits[n]={'vertices':p,'area_m2':area3(p),'z_range_m':[min(x[2] for x in p),max(x[2] for x in p)]}
    if hits:
        rows.append({'triangle_index':tri.index,'polygon_index':tri.polygon_index,'material_slot':o.data.polygons[tri.polygon_index].material_index,'vertex_indices':list(tri.vertices),'vertices_local_xyz':a,'hits':hits})
assert sum('old_pad' in row['hits'] for row in rows)==1,'prior evidence mismatch'
assert sha(src)==lock
q={'status':'READ_ONLY_EXACT_TRIANGLE_CLASSIFICATION','source_sha256':lock,'blender':bpy.app.version_string,'source_meshes':len(old),'object':o.name,'material_slots':[m.name if m else None for m in o.data.materials],'triangles_total':len(o.data.loop_triangles),'volume_definitions':vols,'rows':rows,'counts':{n:sum(n in row['hits'] for row in rows) for n in vols},'limits':['Exact triangle clipping against declared conservative subvolumes only. Assembly, ramp and foundation are envelopes not full designed solids; no runtime collision or relocation. No source save.']}
(out/'v63_conflict.json').write_text(json.dumps(q,indent=2)+'\n');print(q['counts'])
