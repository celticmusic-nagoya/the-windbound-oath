"""Isolated area-first candidate, not adopted or surveyed. Blender 5.3 only."""
import json, math, sys, hashlib
from pathlib import Path

def geometry(d):
    c=d['authored_controls']
    def interp(x, xs, zs):
        for i in range(len(xs)-1):
            if xs[i] <= x <= xs[i+1]:
                f=(x-xs[i])/(xs[i+1]-xs[i]); return zs[i]*(1-f)+zs[i+1]*f
        raise ValueError(x)
    # Deliberately linear interpolation: distinct V02 candidate, not V01 byte reproduction.
    rows=[]
    for j in range(121):
        y=j*2.5
        toe=interp(y,c['north_samples_m'],c['coast_toe_x_m'])
        rim=toe+interp(y,c['rim_offset_north_m'],c['rim_offset_x_m'])
        z=interp(y,c['rim_north_samples_m'],c['rim_z_m'])
        east=c['east_edge_x_m']; edge=18+3*math.sin(math.pi*y/300)
        row=[(toe-12,y,-5),(toe,y,0),(toe+3,y,z*.28),(toe+(rim-toe)*.65,y,z*.72),(rim,y,z)]
        for f in [.07,.14,.21,.30,.40,.50,.60,.70,.80,.90,1.]:
            row.append((rim+(east-rim)*f,y,edge+(z-edge)*(1-f)**3+.6*math.sin(math.pi*f)*math.sin(y/42)))
        assert all(b[0]>a[0] for a,b in zip(row,row[1:]))
        rows.append(row)
    n=len(rows[0]); m=len(rows); v=[p for row in rows for p in row]; N=len(v)
    v += [(x,y,-10) for x,y,z in v[:N]]; faces=[]
    for j in range(m-1):
        for i in range(n-1):
            a=j*n+i; b=a+1; c=a+n+1; e=a+n
            faces.extend([(a,b,c),(a,c,e),(N+a,N+c,N+b),(N+a,N+e,N+c)])
    perimeter=list(range(n))+[j*n+n-1 for j in range(1,m)]+list(range((m-1)*n+n-2,(m-1)*n-1,-1))+[j*n for j in range(m-2,0,-1)]
    for i,a in enumerate(perimeter):
        b=perimeter[(i+1)%len(perimeter)];faces.extend([(a,N+a,N+b),(a,N+b,b)])
    return v,faces

def topology(v,f):
    edges={}
    for a,b,c in f:
        assert len({a,b,c})==3 and all(0<=i<len(v) for i in (a,b,c))
        for i,j in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((i,j))); edges.setdefault(key,[]).append((i,j))
    assert all(len(e)==2 and e[0]==e[1][::-1] for e in edges.values())
    return {'vertices':len(v),'triangles':len(f),'edges':len(edges),'closed_oriented':True}

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    src,out=map(Path,args[:2]); d=json.loads(src.read_text()); v,f=geometry(d); report=topology(v,f)
    if '--check-only' in args: print(json.dumps(report));return
    import bpy
    assert tuple(bpy.app.version)==(5,3,0)
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh=bpy.data.meshes.new('AREA_FIRST_V02');mesh.from_pydata(v,[],f);mesh.update()
    assert not mesh.validate(verbose=True)
    obj=bpy.data.objects.new('AREA_FIRST_V02_UNAPPROVED',mesh);bpy.context.collection.objects.link(obj)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene['candidate_status']='PROVISIONAL_LOCAL_NOT_ADOPTED'
    path=out/'area_first_v02_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    mesh=bpy.data.objects['AREA_FIRST_V02_UNAPPROVED'].data
    reopened=topology([tuple(x.co) for x in mesh.vertices],[tuple(x.vertices) for x in mesh.polygons]);assert reopened==report and sha(path)==before
    report.update(status='ISOLATED_CANDIDATE_NOT_ADOPTED',source_sha256=sha(src),native_sha256=before,reopened=True,interpolation='linear; not V01 reproduction',G1='BLOCKED',G2='NOT_RUN',G3='PARTIAL_NATIVE_REOPEN',G4='NOT_RUN')
    (out/'qa.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
