"""Verify approved Morwen Layer 0 images and register four Blender orthographic reference planes.
Run: blender -b -noaudio --python tools/blender/production_mesh_08/prepare_layer0_references.py
Reference PNGs are REQUIRED; this script never fabricates missing canon.
"""
import hashlib
import json
import math
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "layer0_reference_manifest.json"
OUT = Path("render_output/layer0_reference_setup")
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
records = []
errors = []
for item in data["images"]:
    source = HERE / "references" / item["filename"]
    if not source.is_file():
        errors.append(f"MISSING {item['view']}: {source}")
        continue
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != item["sha256"]:
        errors.append(f"SHA256_MISMATCH {item['view']}: {digest}")
        continue
    try:
        img = bpy.data.images.load(str(source.resolve()), check_existing=False)
        if tuple(img.size) != (item["width"], item["height"]):
            errors.append(f"SIZE_MISMATCH {item['view']}: {tuple(img.size)}")
            bpy.data.images.remove(img)
            continue
        records.append((item, source, img, digest))
    except Exception as exc:
        errors.append(f"INVALID_IMAGE {item['view']}: {exc}")

report = {
    "task": "MORWEN-LAYER0-REFERENCE-SETUP-01",
    "blender_version": bpy.app.version_string,
    "reference_count": len(records),
    "verified_sha256": {item["view"]: digest for item, _, _, digest in records},
    "errors": errors,
    "G1": "BLOCKED" if errors or len(records) != 4 else "REFERENCE_HASH_PASS_VISUAL_NOT_RUN",
    "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN",
}
if errors or len(records) != 4:
    (OUT / "QA.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise RuntimeError("Official Layer 0 PNG prerequisites failed: " + "; ".join(errors))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
collection = bpy.data.collections.new("MORWEN_LAYER0_CANONICAL_REFERENCE_LOCKED")
bpy.context.scene.collection.children.link(collection)
# Each reference image is placed on an upright plane; character faces -Y.
# Front/right/back/left planes face inward, using a consistent 2.0 m body-height guide.
# These planes are VIEW REFERENCES, not a reconstructed or approved mesh.
rotations = {
    "front": (math.pi / 2, 0, 0),
    "right": (math.pi / 2, 0, -math.pi / 2),
    "back": (math.pi / 2, 0, math.pi),
    "left": (math.pi / 2, 0, math.pi / 2),
}
locations = {
    "front": (0, -1.1, 1),
    "right": (1.1, 0, 1),
    "back": (0, 1.1, 1),
    "left": (-1.1, 0, 1),
}
for item, source, img, digest in records:
    view = item["view"]
    bpy.ops.object.empty_add(type="IMAGE", location=locations[view], rotation=rotations[view])
    ob = bpy.context.object
    ob.name = "CANON_LAYER0_" + view.upper()
    ob.data = img
    ob.empty_display_type = "IMAGE"
    ob.empty_display_size = 2.0
    ob.color = (1, 1, 1, 1)
    ob["sha256"] = digest
    ob["source"] = item["filename"]
    ob["canonical_view"] = view
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    collection.objects.link(ob)
    ob.hide_select = True
    ob.hide_render = True
    ob.lock_location = (True, True, True)
    ob.lock_rotation = (True, True, True)
    ob.lock_scale = (True, True, True)

bpy.ops.wm.save_as_mainfile(filepath=str((OUT / "MORWEN_LAYER0_REFERENCES.blend").resolve()))
report["G3"] = "REFERENCE_PLANES_CREATED"
report["source_images_packed"] = False
report["art_qa"] = "NOT_RUN"
(OUT / "QA.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("MORWEN_LAYER0_REFERENCE_SETUP_SUCCESS")
