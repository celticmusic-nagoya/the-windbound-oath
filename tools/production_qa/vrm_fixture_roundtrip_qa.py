#!/usr/bin/env python3
"""Blender-side isolated VRM fixture import/render/roundtrip QA; no canonical assets."""
import bpy
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ.get("TWO_VRM_QA_DIR", "/tmp/morwen-vrm-qa"))
root.mkdir(parents=True, exist_ok=True)
source = root / "basic_armature_vrm1.vrm"
report = {
    "fixture": "saturday06/VRM-Addon-for-Blender v4.10.5 tests/resources/vrm/2.93/out/basic_armature_vrm1.vrm",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None,
    "source_license": "UPSTREAM_LICENSE_MAIN_MIT_OR_GPL_3_0_OR_LATER; FIXTURE_RIGHTS_NOT_INDEPENDENTLY_VERIFIED",
    "blender": bpy.app.version_string,
    "import": "NOT_RUN", "render": "NOT_RUN", "export": "NOT_RUN",
    "reimport": "NOT_RUN", "status": "BLOCKED",
}
def save():
    (root / "qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
try:
    if not source.is_file():
        raise RuntimeError("Missing fixture")
    if not hasattr(bpy.ops.import_scene, "vrm") or not bpy.ops.import_scene.vrm.poll():
        raise RuntimeError("VRM import operator unavailable")
    result = bpy.ops.import_scene.vrm(filepath=str(source))
    if "FINISHED" not in result:
        raise RuntimeError("VRM import returned " + str(result))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    report["mesh_count"] = len(meshes)
    report["armature_count"] = len(arms)
    if not arms:
        raise RuntimeError("No armature imported")
    report["import"] = "PASS"
    # A render requires actual visible mesh geometry; no fabricated success.
    if meshes:
        bpy.ops.object.camera_add(location=(3, -5, 2))
        cam = bpy.context.object
        direction = -cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = cam
        bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.render.filepath = str(root / "fixture_render.png")
        bpy.ops.render.render(write_still=True)
        report["render"] = "PASS" if (root / "fixture_render.png").is_file() else "FAIL"
    else:
        report["render"] = "BLOCKED_NO_MESH"
    # Export only to a throwaway QA directory. Failure is evidence, not a PASS.
    exported = root / "roundtrip.vrm"
    if hasattr(bpy.ops.export_scene, "vrm"):
        try:
            result = bpy.ops.export_scene.vrm(filepath=str(exported))
            if "FINISHED" not in result or not exported.is_file() or exported.stat().st_size == 0:
                raise RuntimeError("VRM export did not produce a nonempty file: " + str(result))
            report["export"] = "PASS"
            report["export_sha256"] = hashlib.sha256(exported.read_bytes()).hexdigest()
            bpy.ops.wm.read_factory_settings(use_empty=True)
            imported = bpy.ops.import_scene.vrm(filepath=str(exported))
            if "FINISHED" not in imported:
                raise RuntimeError("VRM reimport did not finish: " + str(imported))
            report["reimport_armatures"] = sum(o.type == "ARMATURE" for o in bpy.data.objects)
            if report["reimport_armatures"] < 1:
                raise RuntimeError("Roundtrip reimport lost armature")
            report["reimport"] = "PASS"
        except Exception as exc:
            report["roundtrip_error"] = str(exc)
            report["export"] = "FAIL" if report["export"] != "PASS" else "PASS"
            report["reimport"] = "FAIL" if report["export"] == "PASS" else "NOT_RUN"
    else:
        report["export"] = "BLOCKED_OPERATOR_UNAVAILABLE"
    report["status"] = "ROUNDTRIP_PASS" if report["export"] == "PASS" and report["reimport"] == "PASS" else "ROUNDTRIP_INCOMPLETE"
except Exception as exc:
    report["error"] = str(exc)
    report["status"] = "FAIL"
finally:
    save()
    print(json.dumps(report, indent=2))
if report["import"] != "PASS" or report["export"] != "PASS" or report["reimport"] != "PASS":
    raise SystemExit(1)
