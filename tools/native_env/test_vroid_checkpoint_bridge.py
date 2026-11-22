#!/usr/bin/env python3
"""Contract test: #427 session_checkpoint.publish -> bridge -> #468 session_plan.ready (both pinned, SHA-checked).
Uses a synthetic .vroid-shaped zip (v1model/data.bin); no VRoid, no owner files. Usage: test... ENGINE468_DIR ENGINE427_DIR"""
import hashlib, importlib.util, json, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vroid_checkpoint_bridge import to_planner_record  # noqa: E402
PINS = {"session_plan.py": "113212d89784d97ea5b9800951bd1a58bf0afbeedf680f453463a2b9223baaa6",
        "session_checkpoint.py": "c4dd17bf2298ade70ea10436dafa417ebb9ac2c37c9ec4806de192f3f8cb691a"}


def load(d, name):
    p = Path(d) / name
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != PINS[name]:
        raise SystemExit("PIN_MISMATCH %s %s" % (name, got))
    spec = importlib.util.spec_from_file_location(name[:-3], p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


plan, ckpt = load(sys.argv[1], "session_plan.py"), load(sys.argv[2], "session_checkpoint.py")
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    src = t / "work.vroid"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("v1model/data.bin", b"synthetic-not-a-model")
    root = t / "root"
    fp = "a" * 64
    man = ckpt.publish(src, src, root, "face_hair_body", fp)
    stages = [{"id": "face_hair_body", "deps": [], "seconds": 60, "qualified": True, "fingerprint": fp},
              {"id": "wardrobe", "deps": ["face_hair_body"], "seconds": 60, "qualified": True, "fingerprint": "b" * 64}]
    res = {}
    rec = to_planner_record(man, root)  # bytes only
    res["bytes_only_next"] = plan.ready(stages, {"face_hair_body": rec}, root, 3600, 60)
    rec2 = to_planner_record(man, root, {"reopened_sha256": man["sha256"], "observed_values": {"iris_x": 0.141}})
    res["with_app_reopen_next"] = plan.ready(stages, {"face_hair_body": rec2}, root, 3600, 60)
    Path(man["path"]).write_bytes(b"tampered")
    res["tampered_next"] = plan.ready(stages, {"face_hair_body": rec2}, root, 3600, 60)
    ok = (res["bytes_only_next"] == ["face_hair_body"] and res["with_app_reopen_next"] == ["wardrobe"]
          and res["tampered_next"] == ["face_hair_body"])
    res["manifest_keys"] = sorted(man)
    res["result"] = "PASS" if ok else "FAIL"
    print("TWO_VROID_BRIDGE", json.dumps(res))
    assert ok
