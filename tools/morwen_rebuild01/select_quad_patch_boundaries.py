"""Deterministic disk selection around recorded warnings and penetrations."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01'
J=json.loads((Q/'source-mesh.json').read_text());F=J['faces'];P=np.array(J['world']);D=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-local-v01/local-edit.npz');rest=D['original_source_world'];free=D['free_mask']
adj=[set() for _ in F];edgefaces={}
for i,f in enumerate(F):
 for a,b in zip(f,f[1:]+f[:1]):edgefaces.setdefault(tuple(sorted((a,b))),[]).append(i)
for fs in edgefaces.values():
 for i in fs:adj[i].update(set(fs)-{i})
eligible={i for i,f in enumerate(F) if all((D['shoulder_mask']&free)[f])}
warnings={x['face_id'] for x in json.loads((Q/'warning15.json').read_text())};analysis=json.loads((Q/'INDEPENDENT_WARNING_ANALYSIS.json').read_text());pairs=analysis['exact_non_coplanar_penetration_screen']['after_pairs'];selected=warnings|({i for p in pairs for i in p}&eligible)
for _ in range(2):selected|=set().union(*(adj[i] for i in selected))&eligible
centers=np.array([P[f].mean(0) for f in F])
for sign in (1,-1):
 seed=min(eligible,key=lambda i:np.linalg.norm(centers[i]-[sign*.096,.006,.811]));cap={seed}
 for _ in range(3):cap|=set().union(*(adj[i] for i in cap))&eligible
 selected|=cap
components=[];todo=set(selected)
while todo:
 a=min(todo);todo.remove(a);part={a};stack=[a]
 while stack:
  for b in adj[stack.pop()]&todo:todo.remove(b);part.add(b);stack.append(b)
 components.append(sorted(part))
components.sort(key=lambda fs:np.mean(rest[[i for f in fs for i in F[f]],0]),reverse=True);assert len(components)==2
for i,faces in enumerate(components):(Q/f'patch-shoulder-{i}.json').write_text(json.dumps(faces))
for sign in (1,-1):
 faces=[i for i,f in enumerate(F) if np.all((rest[f,2]>.22)&(rest[f,2]<.37)&(rest[f,0]*sign>0)) and rest[f,1].mean()<.025]
 (Q/f'knee-front-{sign}.json').write_text(json.dumps(faces))
print('Two shoulder and two knee disks selected; protected vertices excluded')
