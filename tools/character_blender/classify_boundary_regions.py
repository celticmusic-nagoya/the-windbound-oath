"""Read-only spatial classification of boundary edges in existing Body/Face meshes.
This diagnostic does not claim that disconnected components are defects.
"""
import argparse,hashlib,json,collections
from pathlib import Path
import bpy

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--input",type=Path,required=True)
 p.add_argument("--expected-sha256",required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 if a.out.exists():raise ValueError("Refuse overwrite")
 sha=hashlib.sha256(a.input.read_bytes()).hexdigest()
 if sha!=a.expected_sha256:raise ValueError("SHA mismatch")
 bpy.ops.wm.open_mainfile(filepath=str(a.input.resolve()))
 report={"schema":"TWO_CHARACTER_BOUNDARY_SPATIAL_V1","status":"CANDIDATE_DIAGNOSTIC_ONLY",
  "source_sha256":sha,"blender_version":bpy.app.version_string,"objects":{},
  "neck_region":"NOT_DEFINED_FROM_APPROVED_ANATOMICAL_LANDMARKS",
  "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_MEASUREMENT_ONLY","G4":"NOT_RUN"}
 for name in ("Body","Face"):
  obj=bpy.data.objects[name];mesh=obj.data
  faces_per_edge=collections.Counter()
  for poly in mesh.polygons:
   for key in poly.edge_keys:faces_per_edge[tuple(sorted(key))]+=1
  boundary=[e for e,n in faces_per_edge.items() if n==1]
  adjacency=collections.defaultdict(set)
  for u,v in boundary:adjacency[u].add(v);adjacency[v].add(u)
  unseen=set(adjacency);loops=[]
  while unseen:
   seed=min(unseen);stack=[seed];seen={seed};unseen.remove(seed)
   while stack:
    v=stack.pop()
    for other in adjacency[v]:
     if other not in seen:
      seen.add(other);unseen.discard(other);stack.append(other)
   coords=[obj.matrix_world@mesh.vertices[i].co for i in seen]
   degree_counts=collections.Counter(len(adjacency[i]) for i in seen)
   loops.append({"vertices":len(seen),
    "boundary_edges":sum(len(adjacency[i]) for i in seen)//2,
    "closed_simple_loop":all(len(adjacency[i])==2 for i in seen),
    "degree_histogram":{str(k):v for k,v in sorted(degree_counts.items())},
    "world_bbox_min":[round(min(v[k] for v in coords),6) for k in range(3)],
    "world_bbox_max":[round(max(v[k] for v in coords),6) for k in range(3)]})
  loops.sort(key=lambda x:(-x["boundary_edges"],x["world_bbox_min"]))
  report["objects"][name]={"boundary_edges":len(boundary),"boundary_components":len(loops),
   "boundary_component_summaries":loops,"boundary_vertices":len(adjacency)}
 report["notes"]=["Boundary components are geometric clusters, not automatically errors.",
  "This does not measure correspondence between Body and Face neck seams.",
  "No production mesh was saved or modified."]
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("BOUNDARY_SPATIAL="+json.dumps({k:{"edges":v["boundary_edges"],"components":v["boundary_components"]} for k,v in report["objects"].items()}))
if __name__=="__main__":main()
