"""MAP21-A topology structural checks. No third-party dependencies."""
import json,sys
from pathlib import Path
p=Path(__file__).with_name("map21_topology.json")
d=json.loads(p.read_text(encoding="utf-8"))
nodes={n["id"]:n for n in d["landmarks"]}
assert len(nodes)==len(d["landmarks"]),"duplicate landmark IDs"
assert d["status"]=="PROVISIONAL_NOT_CANON"
assert all(len(n["xy"])==2 and all(isinstance(v,(int,float)) for v in n["xy"]) for n in nodes.values())
graph={n:set() for n in nodes}
for a,b in d["edges"]:
 assert a in nodes and b in nodes and a!=b,(a,b)
 graph[a].add(b);graph[b].add(a)
def reachable(a,b):
 todo=[a];seen=set()
 while todo:
  x=todo.pop()
  if x==b:return True
  if x not in seen:seen.add(x);todo.extend(graph[x]-seen)
 return False
assert all(reachable("village_square",x) for x in nodes),"unreachable landmark"
assert nodes["windwatch_cliff"]["kind"]=="sea_cliff"
assert nodes["riverbank_escape_cliff"]["kind"]=="river_cliff"
assert nodes["windwatch_cliff"]["xy"]!=nodes["riverbank_escape_cliff"]["xy"]
assert nodes["moss_forest"]["xy"][0]>nodes["village_square"]["xy"][0]
assert nodes["moss_forest"]["xy"][1]<nodes["village_square"]["xy"][1]
assert nodes["dunvar_exit"]["xy"][1]>nodes["village_square"]["xy"][1]
assert all(d["constraints"].values())
assert ("return_bend" in graph["windwatch_cliff"]) and ("village_square" in graph["return_bend"])
print(json.dumps({"task":"MAP21-A","result":"PASS","nodes":len(nodes),"edges":len(d["edges"]),"reachability":"PASS","cinematic_occlusion":"NOT_VERIFIED","render_qa":"NOT_RUN"}))
