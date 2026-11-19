"""COMMON-RIG-02: generate a test-only Blender armature from normalized JSON."""
import bpy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/blender/rigs/humanoid_v1.json"
OUTPUT = Path("/tmp/common-rig-02")
OUTPUT.mkdir(parents=True, exist_ok=True)

data = json.loads(SOURCE.read_text(encoding="utf-8"))
bones = data["bones"]
ids = [b["id"] for b in bones]
assert len(ids) == len(set(ids)) == 17, "Unexpected/duplicate bones"
assert data["schema_version"] == 1
by_id = {b["id"]: b for b in bones}
for b in bones:
    assert b["parent"] is None or b["parent"] in by_id, "Missing parent"
    assert len(b["head"]) == len(b["tail"]) == 2
    assert b["head"] != b["tail"], "Zero-length bone"

bpy.ops.wm.read_factory_settings(use_empty=True)
armature = bpy.data.armatures.new("TWO_Humanoid_v1")
rig = bpy.data.objects.new("TWO_Humanoid_v1", armature)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for b in bones:
    eb = armature.edit_bones.new(b["id"])
    # 2D normalized coordinates on XZ plane; positive Y remains zero.
    eb.head = (float(b["head"][0]), 0.0, float(b["head"][1]))
    eb.tail = (float(b["tail"][0]), 0.0, float(b["tail"][1]))
for b in bones:
    if b["parent"] is not None:
        armature.edit_bones[b["id"]].parent = armature.edit_bones[b["parent"]]
bpy.ops.object.mode_set(mode="OBJECT")
assert len(armature.bones) == 17
for b in bones:
    parent = armature.bones[b["id"]].parent
    assert (parent.name if parent else None) == b["parent"]
rig.show_in_front = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "humanoid_v1.blend"))
report = {
    "task": "COMMON-RIG-02",
    "status": "PASS",
    "blender_version": bpy.app.version_string,
    "rig": rig.name,
    "bone_count": len(armature.bones),
    "parent_links": sum(b["parent"] is not None for b in bones),
    "source": "tools/blender/rigs/humanoid_v1.json",
    "production_assets_modified": False,
    "note": "Armature only. No character skin, pose, motion, or rendered sprite."
}
(OUTPUT / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("COMMON_RIG_02_PASS", json.dumps(report))
