"""Audit UVs of the faces that differ from the SHA-pinned Method C carrier.

  blender -b --factory-startup --python c11_uv_audit.py -- CAND.blend METHOD_C.blend OUT.json
"""
import bpy, sys, json, hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c11_uv_qa import island_uv_report  # noqa: E402

cand, mc, out = sys.argv[sys.argv.index("--") + 1:]
T = "Cliff C8 B | joinable coastal segment"
rk = lambda c: (round(c[0], 6), round(c[1], 6), round(c[2], 6))
bpy.ops.wm.open_mainfile(filepath=mc)
m = bpy.data.objects[T].data
cf = {tuple(sorted(rk(m.vertices[i].co) for i in p.vertices)) for p in m.polygons}
bpy.ops.wm.open_mainfile(filepath=cand)
me = bpy.data.objects[T].data
uvl = me.uv_layers.active
co = np.array([v.co[:] for v in me.vertices])
new, ring = [], []
newv = set()
for p in me.polygons:
    if tuple(sorted(rk(me.vertices[i].co) for i in p.vertices)) not in cf:
        new.append(p)
        newv |= set(p.vertices)
for p in me.polygons:
    if p not in new and set(p.vertices) & newv:
        ring.append(p)
newset = {p.index for p in new}
ring = [p for p in me.polygons if p.index not in newset and set(p.vertices) & newv]


def arr(polys):
    t3, tuv = [], []
    for p in polys:
        li = list(p.loop_indices)
        vi = list(p.vertices)
        for k in range(1, len(vi) - 1):   # fan-triangulate
            idx = [0, k, k + 1]
            t3.append(co[[vi[i] for i in idx]])
            tuv.append(np.array([uvl.data[li[i]].uv[:] for i in idx]))
    return np.array(t3).reshape(-1, 3, 3), np.array(tuv).reshape(-1, 3, 2)
n3, nuv = arr(new)
r3, ruv = arr(ring)
rep = island_uv_report(n3, nuv, r3, ruv)
rep["candidate_sha256"] = hashlib.sha256(Path(cand).read_bytes()).hexdigest()
rep["uv_layer"] = uvl.name
Path(out).write_text(json.dumps(rep, indent=2))
print("UV_AUDIT", json.dumps(rep))
