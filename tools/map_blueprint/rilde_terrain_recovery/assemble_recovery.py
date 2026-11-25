"""Read-only assembly for inspection, not the original V03 scene."""
import hashlib,json
from pathlib import Path
import numpy as np,trimesh
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=O/'region_recovery_v02.glb';W=O/'river_water_clipped.glb';B=O.parent/'rilde_recovery/east_river_bridge_reconstructed.glb'
expected=['545c0adb81c82c61dda8d3996d2937bb6257a15cdb9b928f887c1f4fc02eb615','4043fbc171b2b16f138a1b406c2df72846c8fb625fb05ea5ab9e28d8e6f59bcd','83a686b88b556e1f38632f381e433ea7b21b9ceaeedbc5f6e0461de9d8c4e73f'];assert [sha(p) for p in (P,W,B)]==expected
s=trimesh.load(P,force='scene',process=False);t=np.eye(4);t[:3,3]=[300,0,0];w=trimesh.load(W,force='mesh',process=False);s.add_geometry(w,node_name='RIVER_WATER_CLIPPED',geom_name='RIVER_WATER_CLIPPED',transform=t)
b=trimesh.load(B,force='scene',process=False)
for n in b.graph.nodes_geometry:
 a,g=b.graph[n];s.add_geometry(b.geometry[g],node_name=n,geom_name=g,transform=t@a)
p=O/'region_recovery_inspection.glb';p.write_bytes(s.export(file_type='glb'));q=trimesh.load(p,force='scene',process=False);assert len(q.geometry)==14
for n in s.graph.nodes_geometry:
 a,g=s.graph[n];c,h=q.graph[n];assert np.array_equal(s.geometry[g].vertices,q.geometry[h].vertices) and np.array_equal(s.geometry[g].faces,q.geometry[h].faces) and np.allclose(a,c,atol=1e-10,rtol=0)
print(json.dumps(dict(output_sha256=sha(p),script_sha256=sha(Path(__file__)),geometry_count=len(q.geometry),vertices=sum(len(m.vertices) for m in q.geometry.values()),triangles=sum(len(m.faces) for m in q.geometry.values()),source_unchanged=[sha(p) for p in (P,W,B)]==expected),indent=2))
