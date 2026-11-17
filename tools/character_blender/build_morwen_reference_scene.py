"""Build a non-destructive Blender four-view modelling reference scene.

This is a production *reference rig*, not a finished Morwen mesh.
Run: python -m bpy -b --python tools/character_blender/build_morwen_reference_scene.py -- OUTPUT.blend
Images are byte-verified against MANIFEST before opening. Blender version and
source hashes are recorded in a JSON sidecar; source files are never saved over.
"""
import bpy
import hashlib
import json
import pathlib
import sys

SOURCE = pathlib.Path("assets/canonical/morwen/2026-11-16").resolve()
FILES = {
    "front": "LAYER0_FRONT.png",
    "back": "LAYER0_BACK.png",
    "facing_right": "LAYER0_PROFILE_FACING_RIGHT.png",
    "facing_left": "LAYER0_PROFILE_FACING_LEFT.png",
}
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise SystemExit("usage: -- OUTPUT.blend")
dest = pathlib.Path(args[0]).resolve()
if dest.suffix.lower() != ".blend" or SOURCE in dest.parents:
    raise SystemExit("output must be a .blend outside canonical reference directory")

manifest = json.loads((SOURCE / "MANIFEST.json").read_text(encoding="utf-8"))
index = {row["filename"]: row for row in manifest["files"]}
checked = {}
for direction, name in FILES.items():
    path = SOURCE / name
    if not path.is_file() or name not in index:
        raise SystemExit("BLOCKED missing source: " + name)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != index[name]["sha256"]:
        raise SystemExit("BLOCKED source hash mismatch: " + name)
    checked[direction] = {"path": str(path), "sha256": sha}

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != bpy.context.scene.collection.name and collection.users == 0:
        bpy.data.collections.remove(collection)

ref_collection = bpy.data.collections.new("MORWEN_REFERENCE_ONLY_DO_NOT_EXPORT")
bpy.context.scene.collection.children.link(ref_collection)
# Normalized modelling coordinates, NOT canon physical measurements.
# Head/body landmarks are not guessed. All four images share the same height.
reference_height = 2.0
offset = 1.5
for direction, name in FILES.items():
    image = bpy.data.images.load(str(SOURCE / name), check_existing=False)
    image.pack()  # references travel with the candidate .blend; originals remain intact
    image.alpha_mode = "STRAIGHT"
    obj = bpy.data.objects.new("REF_" + direction.upper(), None)
    ref_collection.objects.link(obj)
    obj.empty_display_type = "IMAGE"
    obj.data = image
    obj.empty_display_size = reference_height
    obj.color = (1, 1, 1, 0.6)
    obj.show_in_front = False
    obj.hide_render = True
    # Blender image empties use local XY plane. Place each on the
    # corresponding outward-facing side of the candidate character origin.
    if direction == "front":
        obj.location = (0, -offset, reference_height / 2)
        obj.rotation_euler = (1.5707963267948966, 0, 0)
    elif direction == "back":
        obj.location = (0, offset, reference_height / 2)
        obj.rotation_euler = (1.5707963267948966, 0, 3.141592653589793)
    elif direction == "facing_right":
        obj.location = (offset, 0, reference_height / 2)
        obj.rotation_euler = (1.5707963267948966, 0, 1.5707963267948966)
    else:
        obj.location = (-offset, 0, reference_height / 2)
        obj.rotation_euler = (1.5707963267948966, 0, -1.5707963267948966)
    obj["source_sha256"] = checked[direction]["sha256"]
    obj["source_status"] = "DIRECTOR_REFERENCE_LAYER0"
    obj["physical_scale"] = "UNRESOLVED"
    obj.hide_select = True

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene["project"] = "THE WINDBOUND OATH"
scene["character"] = "Morwen"
scene["asset_status"] = "REFERENCE_SCENE_ONLY"
scene["canonical_precedence"] = "BLOCKED"
scene["gameplay_camera_contract"] = "UNRESOLVED"
scene["body_head_count_target"] = "7.5-8; requires design QA"
scene["garter_leg"] = "anatomical_right"
scene["outer_costume"] = "NOT_MODELLED"
dest.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report = {
    "status": "PASS_REFERENCE_SCENE_ONLY",
    "blend_path": str(dest),
    "blend_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
    "blender_version": bpy.app.version_string,
    "sources": checked,
    "geometry_created": False,
    "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "REFERENCE_SETUP_ONLY", "G4": "NOT_RUN",
}
dest.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "sha256": report["blend_sha256"]}))
