"""Independent stdlib-only normalized macro cliff topology diagnostic.
No Blender, no scan, no canonical dimensions. OBJ is a technical candidate.
"""
import argparse, collections, hashlib, json, math
from pathlib import Path

def build(nx=65,ny=33):
    verts=[]
    for i in range(nx):
        u=i/(nx-1)
        coast=.12*math.sin(2*math.pi*u*1.7)+.055*math.sin(2*math.pi*u*5.1+.4)
        ridge=.13*math.sin(2*math.pi*u*2.2+1)+.05*math.sin(2*math.pi*u*7.3)
        for j in range(ny):
            v=j/(ny-1)
            z=.10+(.90+ridge)*v**.31
            z+=.07*math.sin(u*18+v*9)*math.sin(math.pi*v)**2
            z+=.035*math.sin(u*44+v*20)*math.sin(math.pi*v)**2
            y=1.25*v+coast*(1-v)+.08*math.sin(u*13+v*5)*math.sin(math.pi*v)
            verts.append((u*3.2-1.6,y,z))
    n=len(verts)
    verts.extend((x,y,-.24) for x,y,z in verts[:])
    ix=lambda i,j:i*ny+j
    top=[(ix(i,j),ix(i+1,j),ix(i+1,j+1),ix(i,j+1)) for i in range(nx-1) for j in range(ny-1)]
    faces=top+[tuple(reversed(tuple(n+k for k in f))) for f in top]
    for i in range(nx-1):
        for j in (0,ny-1):
            a,b=ix(i,j),ix(i+1,j)
            faces.append((a,n+a,n+b,b) if j==0 else (b,n+b,n+a,a))
    for j in range(ny-1):
        for i in (0,nx-1):
            a,b=ix(i,j),ix(i,j+1)
            faces.append((b,n+b,n+a,a) if i==0 else (a,n+a,n+b,b))
    return verts,faces

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    verts,faces=build()
    edges=collections.Counter()
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            edges[tuple(sorted((a,b)))]+=1
    boundary=sum(v==1 for v in edges.values())
    nonmanifold=sum(v!=2 for v in edges.values())
    assert boundary==0 and nonmanifold==0,(boundary,nonmanifold)
    assert len(set(faces))==len(faces)
    path=out/"lind_macro_support_normalized.obj"
    with path.open("w") as f:
        f.write("# TECHNICAL ONLY; NON-METRIC; NOT CANONICAL; NOT PRODUCTION READY\n")
        for x,y,z in verts:f.write(f"v {x:.9f} {y:.9f} {z:.9f}\n")
        for face in faces:f.write("f "+" ".join(str(k+1) for k in face)+"\n")
    metrics={"method":"STDLIB_TOPOLOGY_ISOLATION","units":"NORMALIZED_NON_METRIC","production_ready":False,"source_scan_used":False,"vertices":len(verts),"faces":len(faces),"boundary_edges":boundary,"nonmanifold_edges":nonmanifold,"obj_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"G1":"BLOCKED","G2":"NOT_RUN","G3":"PASS_TOPOLOGY_ONLY","G4":"NOT_RUN"}
    (out/"topology_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    print(json.dumps(metrics,indent=2))
if __name__=="__main__":main()
