"""Non-destructive audit of MPFB base.obj: topology islands and source OBJ groups."""
from pathlib import Path
import json,collections
p=Path("_upstream_mpfb/src/mpfb/data/3dobjs/base.obj")
assert p.is_file(),p
verts=[];faces=[];groups=collections.Counter();group="default"
for line in p.open(errors="replace"):
 parts=line.strip().split()
 if not parts:continue
 if parts[0]=="v" and len(parts)>=4:verts.append(tuple(map(float,parts[1:4])))
 elif parts[0] in ("g","o"):group=" ".join(parts[1:]) or "unnamed"
 elif parts[0]=="f":
  ids=[int(t.split("/")[0])-1 for t in parts[1:]]
  faces.append(ids);groups[group]+=1
parent=list(range(len(verts)));size=[1]*len(verts)
def find(i):
 while parent[i]!=i:
  parent[i]=parent[parent[i]];i=parent[i]
 return i
def union(a,b):
 a=find(a);b=find(b)
 if a!=b:
  if size[a]<size[b]:a,b=b,a
  parent[b]=a;size[a]+=size[b]
for f in faces:
 for v in f[1:]:union(f[0],v)
components=collections.defaultdict(list)
for i in range(len(verts)):components[find(i)].append(i)
bounds=[]
for ids in sorted(components.values(),key=len,reverse=True):
 xyz=[verts[i] for i in ids]
 bounds.append({"vertices":len(ids),"min":[min(v[k] for v in xyz) for k in range(3)],"max":[max(v[k] for v in xyz) for k in range(3)]})
edgecount=collections.Counter()
for f in faces:
 for a,b in zip(f,f[1:]+f[:1]):edgecount[tuple(sorted((a,b)))]+=1
report={"source":str(p),"vertices":len(verts),"faces":len(faces),"source_groups":dict(groups),"connected_components":len(components),"components":bounds[:30],"boundary_edges":sum(n==1 for n in edgecount.values()),"nonmanifold_edges":sum(n>2 for n in edgecount.values()),"G2":"NOT_EVALUATED","production_approved":False}
out=Path("render_output/morwen_mpfb_mesh_audit");out.mkdir(parents=True,exist_ok=True)
(out/"mesh_audit.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
