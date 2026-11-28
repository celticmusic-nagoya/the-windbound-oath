"""Independent V94 read-only surface-clearance QA, no native save.
Local Blender units, provisional tolerances, conservative PASS/HOLD/VIOLATION.
"""
import math, sys, json, hashlib, random
from pathlib import Path
def tri_clearance(tri, distance, threshold, *, eps=1e-4, max_depth=7, max_nodes=512):
    if threshold<=eps or eps<=0 or max_depth<0 or max_nodes<1:raise ValueError('limits')
    tri=tuple(tuple(float(x) for x in p) for p in tri)
    if len(tri)!=3 or any(len(p)!=3 or not all(math.isfinite(x) for x in p) for p in tri):raise ValueError('triangle')
    stack=[(tri,0)]; n=0; low=float('inf'); upper=float('inf'); point=None; unresolved=False
    while stack:
        if n>=max_nodes:unresolved=True;low=0.;break
        t,depth=stack.pop(); n+=1
        c=tuple(sum(p[i] for p in t)/3 for i in range(3)); d=float(distance(c))
        if not math.isfinite(d) or d<0:raise ValueError('oracle distance')
        rad=max(math.dist(c,p) for p in t); lb=max(0.,d-rad-eps)
        if d<upper:upper=d;point=c
        if d+eps<threshold:return {'status':'VIOLATION','lower':0.,'upper':upper+eps,'witness':point,'nodes':n}
        if lb>=threshold:low=min(low,lb);continue
        if depth>=max_depth:unresolved=True;low=min(low,lb);continue
        a,b,c=t;mid=lambda u,v:tuple((x+y)*.5 for x,y in zip(u,v));ab,bc,ca=mid(a,b),mid(b,c),mid(c,a)
        stack.extend(((q,depth+1) for q in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca))))
    return {'status':'HOLD' if unresolved else 'PASS','lower':low,'upper':upper+eps,'witness':point,'nodes':n}
def aabb_distance(a,b):
    return math.sqrt(sum(max(0.,a[0][i]-b[1][i],b[0][i]-a[1][i])**2 for i in range(3)))
def bounds(pts):
    return (tuple(min(p[i] for p in pts) for i in range(3)),tuple(max(p[i] for p in pts) for i in range(3)))
def selftest():
    rng=random.Random(94); count=0; stats={}
    for _ in range(2000):
        tri=[(rng.uniform(-.4,.4),rng.uniform(-.4,.4),rng.uniform(-.3,.3)) for i in range(3)]
        z=[p[2] for p in tri];exact=0 if min(z)<=0<=max(z) else min(map(abs,z));r=tri_clearance(tri,lambda p:abs(p[2]),.06)
        assert r['status']!='PASS' or exact>=.06
        assert r['status']!='VIOLATION' or exact<.06
        assert r['lower']<=exact+1e-8 and r['upper']>=exact-1e-8
        stats[r['status']]=stats.get(r['status'],0)+1;count+=3
    t=[(0,0,.01),(.2,0,.205),(0,.2,.205)];assert abs(sum(p[2] for p in t)/3)>.06;assert tri_clearance(t,lambda p:abs(p[2]),.06)['status']=='VIOLATION';count+=2
    assert tri_clearance([(0,0,.06)]*3,lambda p:abs(p[2]),.06,max_nodes=1)['status']=='HOLD';count+=1
    assert abs(aabb_distance(((0,0,0),(1,1,1)),((2,2,2),(3,3,3)))-math.sqrt(3))<1e-12;count+=1
    return dict(cases=2003,assertions=count,plane_classification=stats)
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def native():
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
    lock='e369bdbab0c6301c0168a74fb1082ca850e1f8f0f5a5e6ca9bd805cb74898600'
    assert sha(src)==lock and bpy.app.version[:3]==(5,3,0)
    assert not out.exists();out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
    scene=bpy.context.scene
    deps=bpy.context.evaluated_depsgraph_get()
    objects=sorted(bpy.data.collections['V94_FOREST_FLOOR'].all_objects,key=lambda x:x.name)
    assert len(objects)==9615 and all(o.type=='MESH' for o in objects)
    fx=sorted([o for o in scene.objects if o.name.startswith('V82_FX_') and o.type=='MESH'],key=lambda x:x.name)
    assert {o.name for o in fx}=={'V82_FX_01_stele','V82_FX_02_posts','V82_FX_03_floor'}
    # Read raw mesh transforms; any modifier invalidates the raw-geometry proof.
    assert all(not o.modifiers for o in fx+objects)
    fv=[];fp=[];fb=[]
    for o in fx:
        v=[tuple(o.matrix_world@x.co) for x in o.data.vertices];o.data.calc_loop_triangles()
        assert v
        fb.append(bounds(v));base=len(fv);fv.extend(v);fp.extend(tuple(base+i for i in t.vertices) for t in o.data.loop_triangles)
    bvh=BVHTree.FromPolygons([Vector(v) for v in fv],fp,all_triangles=True)
    def dist(p):
        hit,normal,index,d=bvh.find_nearest(Vector(p))
        assert hit is not None and d is not None
        return d
    # V92 particle motion envelope from verified root-local glTF axes x,y(up),z.
    # Blender maps (x,-z,y); conservative union box, not collision verdict.
    cx,cy,cz=93.94316101074219,-93.07432556152344,28.604717254638672
    mote_box=((cx-1.16,cy-1.16,cz+.06),(cx+1.16,cy+1.16,cz+1.88))
    groups={};possible_mote=[];worst=[];ntri=0
    qa={'source_sha256':lock,'object_count':len(objects),'fx_count':len(fx),'fx_triangles':len(fp),'test':selftest(),'groups':groups,'mote_sweep_aabb':mote_box,'limits':['Distance oracle is Blender float BVH; provisional epsilon .0001, not calibrated exact arithmetic','Threshold .06 for ivy/all other dressing, .12 ledge moss','HOLD when subdivision budget exhausted; witness denotes near surface not necessarily intersection','Mote sweep AABB overlap is potential only, not exact moving-particle collision','Raw mesh transforms only, no modifiers allowed','No traversal or game QA']}
    def checkpoint():
        qa['triangles_accounted']=ntri;qa['mote_aabb_candidates']=possible_mote;qa['witnesses']=sorted(worst,key=lambda x:x['upper'])[:100]
        (out/'v94_clearance_qa.json').write_text(json.dumps(qa,indent=2,allow_nan=False))
    for j,o in enumerate(objects):
        name=o.name;kind=name.removeprefix('V94_').rsplit('_',1)[0] if name.rsplit('_',1)[-1].isdigit() else name.removeprefix('V94_')
        threshold=.12 if kind=='ledge_moss' else .06
        g=groups.setdefault(kind,dict(objects=0,triangles=0,broadphase_clear_triangles=0,pass_triangles=0,hold_triangles=0,violation_triangles=0,queries=0))
        g['objects']+=1;o.data.calc_loop_triangles();nt=len(o.data.loop_triangles);g['triangles']+=nt;ntri+=nt
        ob=bounds([tuple(o.matrix_world@Vector(p)) for p in o.bound_box])
        mote_near=aabb_distance(ob,mote_box)<=.0001
        if mote_near:possible_mote.append({'object':name,'kind':kind,'bounds':ob})
        if min(aabb_distance(ob,b) for b in fb)>=threshold+.0001:g['broadphase_clear_triangles']+=nt;continue
        verts=[tuple(o.matrix_world@v.co) for v in o.data.vertices]
        for t in o.data.loop_triangles:
            tri=tuple(verts[i] for i in t.vertices);tb=bounds(tri)
            if min(aabb_distance(tb,b) for b in fb)>=threshold+.0001:g['broadphase_clear_triangles']+=1;continue
            res=tri_clearance(tri,dist,threshold);g['queries']+=res['nodes'];g[res['status'].lower()+'_triangles']+=1
            if res['status']!='PASS':
                worst.append(dict(object=name,kind=kind,threshold=threshold,triangle=t.index,**res))
                if len(worst)>200:worst=sorted(worst,key=lambda x:x['upper'])[:100]
        if j%100==0:checkpoint()
    assert all(g['triangles']==sum(g[k] for k in ('broadphase_clear_triangles','pass_triangles','hold_triangles','violation_triangles')) for g in groups.values())
    assert sha(src)==lock;qa['source_unchanged']=True;qa['complete']=True
    checkpoint();print('V94_CLEARANCE_DONE',json.dumps(qa,allow_nan=False),flush=True)
if __name__=='__main__':
    if '--self-test' in sys.argv:print(json.dumps(selftest()))
    else:native()
