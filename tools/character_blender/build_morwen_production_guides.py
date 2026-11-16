"""Create immutable-source-backed sculpting guides; NOT a production character.

Run with installed bpy: python tools/character_blender/build_morwen_production_guides.py -- OUT.blend
"""
import bpy
import hashlib
import json
import pathlib
import sys

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise SystemExit("usage: -- OUT.blend")
root = pathlib.Path("assets/canonical/morwen/2026-11-16").resolve()
out = pathlib.Path(args[0]).resolve()
if out.suffix != ".blend" or root in out.parents:
    raise SystemExit("BLOCKED invalid output path")
manifest = json.loads((root / "MANIFEST.json").read_text())
index = {f["filename"]: f for f in manifest["files"]}
names = ["MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg", "LAYER0_FRONT.png",
         "LAYER0_BACK.png", "LAYER0_PROFILE_FACING_RIGHT.png",
         "LAYER0_PROFILE_FACING_LEFT.png"]
for name in names:
    p = root / name
    if hashlib.sha256(p.read_bytes()).hexdigest() != index[name]["sha256"]:
        raise SystemExit("BLOCKED SHA mismatch: " + name)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
collection = bpy.data.collections.new("REFERENCE_ONLY__DO_NOT_EXPORT")
bpy.context.scene.collection.children.link(collection)
# Image empties are editable reference cards, never character geometry.
cards = [
    ("FRONT", names[1], (-2.0, 0.0, 1.0), (1.57079632679, 0, 0)),
    ("BACK", names[2], (2.0, 0.0, 1.0), (1.57079632679, 0, 0)),
    ("RIGHT", names[3], (0.0, -2.0, 1.0), (1.57079632679, 0, 1.57079632679)),
    ("LEFT", names[4], (0.0, 2.0, 1.0), (1.57079632679, 0, 1.57079632679)),
]
for direction, filename, location, rotation in cards:
    img = bpy.data.images.load(str(root / filename), check_existing=False)
    img.pack()
    empty = bpy.data.objects.new("REF_" + direction, None)
    empty.empty_display_type = "IMAGE"
    empty.data = img
    empty.empty_display_size = 2.0
    empty.location = location
    empty.rotation_euler = rotation
    empty.hide_render = True
    empty["sha256"] = index[filename]["sha256"]
    collection.objects.link(empty)
# The 7.5–8 head target is a guide ratio, not a claim that the supplied
# Layer0 images themselves have this proportion.
guide = bpy.data.collections.new("PROPORTION_GUIDES__NON_ANATOMICAL")
bpy.context.scene.collection.children.link(guide)
for count in (7.5, 8.0):
    for step in range(9):
        z = min(2.0, 2.0 * step / count)
        curve = bpy.data.curves.new("guide_%s_%s" % (count, step), "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.002
        poly = curve.splines.new("POLY")
        poly.points.add(1)
        poly.points[0].co = (-0.6, 0, z, 1)
        poly.points[1].co = (0.6, 0, z, 1)
        obj = bpy.data.objects.new("HEAD_RATIO_%s_LEVEL_%s" % (count, step), curve)
        obj["status"] = "RATIO_GUIDE_ONLY"
        guide.objects.link(obj)
scene = bpy.context.scene
scene["asset_status"] = "SCULPTING_GUIDES_ONLY"
scene["character_geometry"] = "NOT_CREATED"
scene["G1"] = "BLOCKED"
scene["G2"] = "NOT_RUN"
scene["G4"] = "NOT_RUN"
scene["reference_design_sha256"] = index[names[0]]["sha256"]
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report = {
    "status": "PASS_REFERENCE_GUIDES_ONLY",
    "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    "source_sha256": {name: index[name]["sha256"] for name in names},
    "reference_cards": 4, "head_ratio_guides": [7.5, 8.0],
    "character_geometry_created": False, "art_qa": "NOT_RUN",
    "design_match": "BLOCKED", "game_qa": "NOT_RUN",
}
out.with_suffix(".json").write_text(json.dumps(report, indent=2))
print(json.dumps({"status": report["status"], "cards": 4}))
