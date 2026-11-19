"""MORWEN-RIG-09: import reviewed-format candidate anchor JSON into Blender.

Creates four *separate* 2D armatures. No sprite, skin, image or canonical asset.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/blender"))
from qa_morwen_anchors import validate

EDGES = [
    ("head", "shoulder.L"), ("head", "shoulder.R"),
    ("shoulder.L", "elbow.L"), ("elbow.L", "wrist.L"),
    ("shoulder.R", "elbow.R"), ("elbow.R", "wrist.R"),
    ("shoulder.L", "pelvis"), ("shoulder.R", "pelvis"),
    ("pelvis", "knee.L"), ("knee.L", "ankle.L"),
    ("pelvis", "knee.R"), ("knee.R", "ankle.R")
]

def build(data, output_dir):
    errors = validate(data, require_measured=True)
    if errors:
        raise ValueError("; ".join(errors))
    if data.get("status") != "MEASURED_CANDIDATE_UNREVIEWED":
        raise ValueError("Unexpected approval status; requires candidate JSON")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    summary = {}
    for index, (facing, entry) in enumerate(data["facings"].items()):
        arm = bpy.data.armatures.new("Morwen_" + facing + "_candidate")
        obj = bpy.data.objects.new(arm.name, arm)
        bpy.context.collection.objects.link(obj)
        obj.location.x = index * 1.5
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        for a,b in EDGES:
            p,q = entry["anchors"][a], entry["anchors"][b]
            # Pixel coordinate Y increases downward; Blender Z increases upward.
            head=(float(p["x"])-0.5, 0, 1.0-float(p["y"]))
            tail=(float(q["x"])-0.5, 0, 1.0-float(q["y"]))
            if sum((x-y)**2 for x,y in zip(head,tail)) < 1e-10:
                raise ValueError(f"{facing}: zero-length segment {a}->{b}")
            bone=arm.edit_bones.new(a + "__" + b)
            bone.head=head
            bone.tail=tail
        bpy.ops.object.mode_set(mode="OBJECT")
        obj["facing"]=facing
        obj["approval_status"]="CANDIDATE_UNREVIEWED"
        obj.show_in_front=True
        summary[facing]={"segments":len(arm.bones),"source":entry["source"]}
    output_dir.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir/"morwen_measured_candidate.blend"))
    report={"task":"MORWEN-RIG-09","status":"PASS","facings":summary,
            "production_assets_modified":False,"source_images_imported":False,
            "visual_approval":False}
    (output_dir/"qa.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("MORWEN_RIG_09_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--anchors",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    build(json.loads(args.anchors.read_text(encoding="utf-8")),args.output_dir)
