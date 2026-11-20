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
def stage(name):
    report["current_stage"] = name
    save()
    print("VRM_QA_STAGE " + name, flush=True)
try:
    if not source.is_file():
        raise RuntimeError("Missing fixture")
    if not hasattr(bpy.ops.import_scene, "vrm") or not bpy.ops.import_scene.vrm.poll():
        raise RuntimeError("VRM import operator unavailable")
    stage("import_start")
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
    stage("import_pass")
    # Export only to a throwaway QA directory. Failure is evidence, not a PASS.
    exported = root / "roundtrip.vrm"
    if hasattr(bpy.ops.export_scene, "vrm"):
        try:
            stage("export_start")
            result = bpy.ops.export_scene.vrm(filepath=str(exported))
            if "FINISHED" not in result or not exported.is_file() or exported.stat().st_size == 0:
                raise RuntimeError("VRM export did not produce a nonempty file: " + str(result))
            report["export"] = "PASS"
            report["export_sha256"] = hashlib.sha256(exported.read_bytes()).hexdigest()
            # Keep the registered VRM extension enabled; factory reset would disable it.
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete(use_global=False)
            for armature in list(bpy.data.armatures):
                if armature.users == 0:
                    bpy.data.armatures.remove(armature)
            stage("reimport_start")
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
    stage("roundtrip_complete")
    # Use software CPU Cycles instead of headless EEVEE/Vulkan/EGL on GitHub runners.
    # The prior EEVEE attempt crashed after import (exit 134, missing libEGL.so.1).
    # Test the actual mesh currently present after export/reimport.
    render_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if render_meshes:
        try:
            bpy.ops.object.camera_add(location=(3, -5, 2))
            cam = bpy.context.object
            direction = -cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            bpy.context.scene.camera = cam
            bpy.context.scene.render.engine = "CYCLES"
            bpy.context.scene.cycles.device = "CPU"
            bpy.context.scene.cycles.samples = 16
            bpy.context.scene.render.resolution_x = 512
            bpy.context.scene.render.resolution_y = 512
            bpy.context.scene.render.resolution_percentage = 100
            bpy.context.scene.render.image_settings.file_format = "PNG"
            bpy.context.scene.render.filepath = str(root / "fixture_render.png")
            stage("render_cpu_cycles_start")
            bpy.ops.render.render(write_still=True)
            stage("render_cpu_cycles_returned")
            report["render"] = "PASS" if (root / "fixture_render.png").is_file() else "FAIL_NO_PNG"
        except Exception as exc:
            report["render"] = "FAIL"
            report["render_error"] = str(exc)
    else:
        report["render"] = "BLOCKED_NO_MESH"
    if report["export"] == "PASS" and report["reimport"] == "PASS" and report["render"] == "PASS":
        report["status"] = "FULL_FIXTURE_QA_PASS"
    elif report["export"] == "PASS" and report["reimport"] == "PASS":
        report["status"] = "ROUNDTRIP_PASS_RENDER_INCOMPLETE"
    else:
        report["status"] = "ROUNDTRIP_INCOMPLETE"
except Exception as exc:
    report["error"] = str(exc)
    report["status"] = "FAIL"
finally:
    save()
    print(json.dumps(report, indent=2))
if report["import"] != "PASS" or report["export"] != "PASS" or report["reimport"] != "PASS" or report["render"] != "PASS":
    raise SystemExit(1)
