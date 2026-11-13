"""Read-only reusable Blender mesh topology report. Never modifies source meshes."""
import bpy, json, argparse
from collections import defaultdict, deque
from pathlib import Path

def audit(mesh):
 vertices=len(mesh.vertices); edges=len(mesh.edges); faces=len(mesh.polygons)
 counts=defaultdict(int)
 adjacency=[set() for _ in range(vertices)]
 for e in mesh.edges:
  a,b=e.vertices
  adjacency[a].add(b);adjacency[b].add(a)
 for poly in mesh.polygons:
  counts[len(poly.vertices)]+=1
 edge_faces=defaultdict(int)
 for poly in mesh.polygons:
  for key in poly.edge_keys:edge_faces[tuple(sorted(key))]+=1
 boundary=sum(v==1 for v in edge_faces.values())
 nonmanifold=sum(v>2 for v in edge_faces.values())
 loose_edges=sum(tuple(sorted(e.vertices)) not in edge_faces for e in mesh.edges)
 seen=set();components=[];component_details=[]
 for start in range(vertices):
  if start in seen:continue
  queue=deque([start]);seen.add(start);size=0;members=[]
  while queue:
   v=queue.popleft();size+=1;members.append(v)
   for neighbor in adjacency[v]:
    if neighbor not in seen:seen.add(neighbor);queue.append(neighbor)
  components.append(size)
  coords=[mesh.vertices[i].co for i in members]
  mins=[min(c[k] for c in coords) for k in range(3)]
  maxs=[max(c[k] for c in coords) for k in range(3)]
  component_details.append({"vertices":size,"min_xyz":[round(float(v),5) for v in mins],"max_xyz":[round(float(v),5) for v in maxs],"vertex_index_sample":members[:8]})
 return {"vertices":vertices,"edges":edges,"faces":faces,
 "triangles":sum(max(0,len(p.vertices)-2) for p in mesh.polygons),
 "face_sides":dict(sorted(counts.items())),
 "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
 "loose_edges":loose_edges,"connected_components":len(components),
 "component_vertex_counts":sorted(components,reverse=True),
 "component_details":sorted(component_details,key=lambda x:x["vertices"],reverse=True),
 "uv_layers":len(mesh.uv_layers),"materials":len(mesh.materials),
 "qa_status":"MEASURED_NOT_ART_APPROVED"}

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--output",required=True)
 parser.add_argument("--name",default="")
 args=parser.parse_args()
 meshes=[o for o in bpy.data.objects if o.type=="MESH" and (not args.name or o.name==args.name)]
 assert meshes,"No meshes selected for read-only audit"
 result={"schema":"TWO-MESH-TOPOLOGY-AUDIT-01","source_modified":False,
 "meshes":{o.name:audit(o.data) for o in meshes}}
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("Mesh topology audit:",len(meshes),"objects")
if __name__=="__main__":main()
