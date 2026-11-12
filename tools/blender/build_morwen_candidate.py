"""MORWEN-RIG-03: validate candidate profile and attach placeholder empties."""
import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "tools/blender/profiles/morwen_v1.json"
RIG_PATH = ROOT / "tools/blender/rigs/humanoid_v1.json"
OUT = Path("/tmp/morwen-rig-03")
OUT.mkdir(parents=True, exist_ok=True)

profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
rig_data = json.loads(RIG_PATH.read_text(encoding="utf-8"))
assert profile["status"] == "CANDIDATE_ONLY"
assert profile["reference_policy"]["canonical_binary_available"] is False
assert profile["reference_policy"]["do_not_mirror_asymmetric_details"] is True
assert profile["facings"] == ["front","left","right","back"]
assert profile["scale"]["status"] == "PLACEHOLDER_NOT_MEASURED"
bones = rig_data["bones"]
ids = {b["id"] for b in bones}
assert len(ids) == 17
attachments = profile["attachments"]
assert len({a["id"] for a in attachments}) == len(attachments)
assert all(a["bone"] in ids for a in attachments)
assert all(a["status"] != "APPROVED" for a in attachments)

bpy.ops.wm.read_factory_settings(use_empty=True)
armature = bpy.data.armatures.new("Morwen_Prototype_Armature")
obj = bpy.data.objects.new("Morwen_Prototype_Rig", armature)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for b in bones:
    eb = armature.edit_bones.new(b["id"])
    eb.head = (b["head"][0], 0.0, b["head"][1])
    eb.tail = (b["tail"][0], 0.0, b["tail"][1])
for b in bones:
    if b["parent"]:
        armature.edit_bones[b["id"]].parent = armature.edit_bones[b["parent"]]
bpy.ops.object.mode_set(mode="OBJECT")
obj.show_in_front = True
for attachment in attachments:
    empty = bpy.data.objects.new("CANDIDATE_" + attachment["id"], None)
    bpy.context.collection.objects.link(empty)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.04
    empty.parent = obj
    empty.parent_type = "BONE"
    empty.parent_bone = attachment["bone"]
    empty["approval_status"] = attachment["status"]
assert len(armature.bones) == 17
assert sum(o.name.startswith("CANDIDATE_") for o in bpy.data.objects) == len(attachments)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "morwen_rig_candidate.blend"))
report = {
    "task": "MORWEN-RIG-03",
    "status": "PASS",
    "bone_count": len(armature.bones),
    "placeholder_attachments": len(attachments),
    "canon_image_imported": False,
    "pose_or_sprite_rendered": False,
    "production_assets_modified": False
}
(OUT / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("MORWEN_RIG_03_PASS", json.dumps(report))
