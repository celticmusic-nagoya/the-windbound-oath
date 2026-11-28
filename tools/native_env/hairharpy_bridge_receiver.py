"""Blender 5.3.0 receiver for a real HairHarpy GUI "Send" (background mode).

Loads the HairHarpy v2.0.0 bridge add-on (tag source, hash-checked by caller), listens on 127.0.0.1:8790 and runs the
add-on's own main-thread pump until one /send has been applied (or timeout), then saves a native .blend.
Usage: blender -b --factory-startup --python hairharpy_bridge_receiver.py -- ADDON.py OUT.blend REPORT.json TIMEOUT_S
"""
import importlib.util
import json
import sys
import time

import bpy

addon, out_blend, report, timeout = sys.argv[sys.argv.index("--") + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True)  # receive into an empty scene
spec = importlib.util.spec_from_file_location("hmc_bridge_blender", addon)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.register()
received = []
orig_build = mod.build


def build(data):  # wrap only to record what arrived; geometry is built by the add-on's own build()
    received.append({"app": data.get("app"), "v": data.get("v"), "up": data.get("up"),
                     "objects": [{"name": o.get("name"), "points": len(o.get("pos") or []) // 3,
                                  "faces": len(o.get("faces") or [])} for o in data.get("objects", [])]})
    return orig_build(data)


mod.build = build
assert mod.start(8790), mod._state
print("TWO_HH_RECEIVER_LISTENING", flush=True)
end = time.monotonic() + float(timeout)
while not received and time.monotonic() < end:
    mod._pump()
    time.sleep(0.05)
for _ in range(20):  # let the add-on finish the job and reply
    mod._pump()
    time.sleep(0.05)
mod.stop()
coll = bpy.data.collections.get("HairMesh")
objs = []
for o in (coll.objects if coll else []):
    me = o.data
    objs.append({"name": o.name, "vertices": len(me.vertices), "faces": len(me.polygons),
                 "quads": sum(1 for p in me.polygons if len(p.vertices) == 4),
                 "dimensions": [round(x, 5) for x in o.dimensions]})
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
res = {"blender": bpy.app.version_string, "received_payloads": received, "objects": objs,
       "result": "PASS" if received and objs else "FAIL_NO_SEND_RECEIVED"}
open(report, "w").write(json.dumps(res, indent=1))
print("TWO_HH_RECEIVER", res["result"], flush=True)
