"""Independent, fail-closed oriented topology QA for generated OBJ meshes.

No Blender and no geometry mutation. Technical gate only, never art approval.
"""
import argparse
import collections
import json
import math
from pathlib import Path

def inspect(path):
    vertices=[]
    faces=[]
    for raw in Path(path).read_text().splitlines():
        if raw.startswith("v "):
            vertices.append(tuple(float(x) for x in raw.split()[1:4]))
        elif raw.startswith("f "):
            faces.append(tuple(int(x.split("/")[0])-1 for x in raw.split()[1:]))
    if not vertices or not faces:
        raise ValueError("Empty mesh")
    directed=collections.Counter()
    undirected=collections.Counter()
    adj=[set() for _ in vertices]
    volume6=0.
    degenerate=0
    for face in faces:
        if len(face)<3 or len(set(face))!=len(face) or any(i<0 or i>=len(vertices) for i in face):
            degenerate+=1
            continue
        for a,b in zip(face,face[1:]+face[:1]):
            directed[(a,b)]+=1
            undirected[tuple(sorted((a,b)))]+=1
            adj[a].add(b);adj[b].add(a)
        p=vertices[face[0]]
        for k in range(1,len(face)-1):
            q=vertices[face[k]]
            r=vertices[face[k+1]]
            cross=(q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0])
            volume6+=p[0]*cross[0]+p[1]*cross[1]+p[2]*cross[2]
            u=[q[i]-p[i] for i in range(3)]
            v=[r[i]-p[i] for i in range(3)]
            cr=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if sum(x*x for x in cr)<1e-20:degenerate+=1
    seen=set()
    components=0
    used={v for f in faces for v in f}
    for root in sorted(used):
        if root in seen:continue
        components+=1
        stack=[root];seen.add(root)
        while stack:
            for n in adj[stack.pop()]:
                if n not in seen:seen.add(n);stack.append(n)
    orientation_conflicts=sum(1 for (a,b),count in undirected.items() if count==2 and (directed[(a,b)]!=1 or directed[(b,a)]!=1))
    result={"vertices":len(vertices),"faces":len(faces),"components":components,"boundary_edges":sum(c==1 for c in undirected.values()),"nonmanifold_edges":sum(c!=2 for c in undirected.values()),"orientation_conflicts":orientation_conflicts,"degenerate_triangles":degenerate,"signed_volume":volume6/6,"isolated_vertices":len(vertices)-len(used)}
    result["pass"]=result["components"]==1 and result["nonmanifold_edges"]==0 and result["orientation_conflicts"]==0 and result["degenerate_triangles"]==0 and result["isolated_vertices"]==0 and math.isfinite(result["signed_volume"]) and result["signed_volume"]>1e-8
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--obj",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    result=inspect(a.obj)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if not result["pass"]:raise SystemExit(1)

if __name__=="__main__":main()
