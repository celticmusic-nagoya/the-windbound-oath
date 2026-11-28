"""HairHarpy v2.0.0 Blender bridge interoperability probe (Blender 5.3.0, background).

Loads the add-on file shipped with the HairHarpy release (hash-checked by the caller), starts its real HTTP
server and drives its real main-thread job pump (bpy timers do not run in -b, so _pump() is called in a loop).
A client thread sends /ping and /send with a payload in HairHarpy's v1 wire format (Export.cpp bridgePayload,
tag v2.0.0). The payload geometry is SYNTHETIC: a GUI-made HairHarpy mesh Send is NOT_RUN here.
Usage: blender -b --factory-startup --python hairharpy_bridge_probe.py -- ADDON.py OUT.blend REPORT.json
"""
import importlib.util
import json
import math
import sys
import threading
import time
import urllib.request

import bpy

addon, out_blend, report = sys.argv[sys.argv.index("--") + 1:][:3]
spec = importlib.util.spec_from_file_location("hmc_bridge_blender", addon)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.register()
PORT = 8790
assert mod.start(PORT), mod._state


def strands():
    objs = []
    for s in range(3):  # three ribbon cards, Y-up like HairHarpy
        pos, faces, rows, cols = [], [], 12, 4
        for r in range(rows + 1):
            t = r / rows
            y = 1.6 - 0.9 * t
            cx = (s - 1) * 0.12 + 0.05 * math.sin(t * 3.0 + s)
            for c in range(cols + 1):
                u = c / cols - 0.5
                pos += [cx + u * 0.08 * (1 - 0.7 * t), y, 0.12 + 0.03 * math.cos(t * 2)]
        for r in range(rows):
            for c in range(cols):
                a = r * (cols + 1) + c
                faces.append([a, a + 1, a + cols + 2, a + cols + 1])
        objs.append({"name": "HH_probe_strand_%d" % s, "pos": pos, "faces": faces})
    return {"app": "hmc", "v": 1, "replace": True, "up": "y", "objects": objs}


payload = strands()
results = {}


def client():
    def call(cmd, body):
        req = urllib.request.Request("http://127.0.0.1:%d/%s" % (PORT, cmd), data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    results["ping"] = call("ping", {})
    results["send"] = call("send", payload)


th = threading.Thread(target=client, daemon=True)
th.start()
end = time.monotonic() + 60
while th.is_alive() and time.monotonic() < end:
    mod._pump()
    time.sleep(0.05)
mod.stop()

coll = bpy.data.collections.get("HairMesh")
got = []
for o in (coll.objects if coll else []):
    zs = [v.co.z for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    got.append({"name": o.name, "vertices": len(o.data.vertices), "faces": len(o.data.polygons),
                "z_range": [round(min(zs), 5), round(max(zs), 5)], "y_range": [round(min(ys), 5), round(max(ys), 5)]})
exp = [{"name": o["name"], "vertices": len(o["pos"]) // 3, "faces": len(o["faces"])} for o in payload["objects"]]
ok_counts = sorted((g["name"], g["vertices"], g["faces"]) for g in got) == sorted((e["name"], e["vertices"], e["faces"]) for e in exp)
# Y-up -> Z-up: program y (0.7..1.6) must become Blender z; program z (~0.12) must become Blender -y
ok_axes = all(0.69 < g["z_range"][0] and g["z_range"][1] < 1.61 and g["y_range"][1] < 0 for g in got)
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
res = {"blender": bpy.app.version_string, "ping": results.get("ping"), "send_status": (results.get("send") or [None])[0],
       "send_reply": (results.get("send") or [None, None])[1], "received": got, "expected": exp,
       "counts_match": ok_counts, "axis_conversion_ok": ok_axes, "payload": "SYNTHETIC_V1_WIRE_FORMAT",
       "gui_send_from_hairharpy": "NOT_RUN", "result": "PASS" if ok_counts and ok_axes and results.get("send", [0])[0] == 200 else "FAIL"}
open(report, "w").write(json.dumps(res, indent=1))
print("TWO_HH_BRIDGE", res["result"])
