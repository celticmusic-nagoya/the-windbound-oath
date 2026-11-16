"""Build a reversible 3D silhouette envelope from four SHA-verified Layer0 references.

This is a NON-ANATOMICAL geometric measurement surface, not a Morwen character
mesh, rig, costume, or approved production asset. Use to constrain sculpting.
Run: python tools/character_blender/build_morwen_silhouette_envelope.py -- OUT.blend
"""
import hashlib
import json
import math
import pathlib
import sys

import bpy
from PIL import Image

ROOT = pathlib.Path("assets/canonical/morwen/2026-11-16").resolve()
VIEWS = {
    "front": "LAYER0_FRONT.png",
    "back": "LAYER0_BACK.png",
    "right": "LAYER0_PROFILE_FACING_RIGHT.png",
    "left": "LAYER0_PROFILE_FACING_LEFT.png",
}
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise SystemExit("usage: -- OUT.blend")
out = pathlib.Path(args[0]).resolve()
if out.suffix != ".blend" or ROOT in out.parents:
    raise SystemExit("BLOCKED invalid output destination")
manifest = json.loads((ROOT / "MANIFEST.json").read_text())
index = {f["filename"]: f for f in manifest["files"]}
samples = {}
for direction, filename in VIEWS.items():
    path = ROOT / filename
    if hashlib.sha256(path.read_bytes()).hexdigest() != index[filename]["sha256"]:
        raise SystemExit("BLOCKED source SHA: " + filename)
    with Image.open(path) as img:
        if img.mode != "RGBA" or img.size != (384, 1024):
            raise SystemExit("BLOCKED source format: " + filename)
        alpha = img.getchannel("A")
        # Strong opacity threshold excludes antialias fringe; no anatomy inferred.
        rows = []
        for y in range(1024):
            values = [x for x in range(384) if alpha.getpixel((x, y)) >= 224]
            rows.append((min(values), max(values)) if values else None)
        samples[direction] = rows

# A paired silhouette cannot establish front/back anatomical correspondence.
# Use conservative union of opposite views and record that limitation.
def bounds_at(y, directions):
    pairs = [samples[d][y] for d in directions if samples[d][y] is not None]
    if not pairs:
        return None
    return min(p[0] for p in pairs), max(p[1] for p in pairs)

rows = []
for y in range(0, 1024, 4):
    fb = bounds_at(y, ("front", "back"))
    side = bounds_at(y, ("right", "left"))
    if fb is None or side is None:
        continue
    # Both image sets have equal pixel dimensions, but this scale is a
    # normalized sculpting coordinate system, NOT verified physical size.
    z = (1023 - y) / 1023 * 2.0
    xcenter = (fb[0] + fb[1] - 383) / 383
    ycenter = (side[0] + side[1] - 383) / 383
    rx = max(0.008, (fb[1] - fb[0] + 1) / 383)
    ry = max(0.008, (side[1] - side[0] + 1) / 383)
    rows.append((z, xcenter, ycenter, rx, ry))
if len(rows) < 100:
    raise SystemExit("BLOCKED insufficient overlapping silhouette rows")
rows.sort()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
verts = []
faces = []
segments = 32
for z, cx, cy, rx, ry in rows:
    for j in range(segments):
        t = 2 * math.pi * j / segments
        verts.append((cx + rx * math.cos(t), cy + ry * math.sin(t), z))
for i in range(len(rows) - 1):
    for j in range(segments):
        a = i * segments + j
        b = i * segments + (j + 1) % segments
        faces.append((a, b, b + segments, a + segments))
faces.append(tuple(reversed(range(segments))))
faces.append(tuple((len(rows) - 1) * segments + j for j in range(segments)))
mesh = bpy.data.meshes.new("SilhouetteEnvelopeMeasured")
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new("QA_ONLY_SILHOUETTE_ENVELOPE_NOT_CHARACTER", mesh)
bpy.context.collection.objects.link(obj)
for polygon in mesh.polygons:
    polygon.use_smooth = True
obj["source"] = "four director Layer0 images; SHA256 checked"
obj["status"] = "NON_ANATOMICAL_QA_ENVELOPE"
obj["art_approval"] = "NOT_RUN"
obj["canonical_design_match"] = "BLOCKED"
obj["garter_geometry"] = "NOT_MODELLED"
obj["outer_costume"] = "NOT_MODELLED"
scene = bpy.context.scene
scene["asset_status"] = "MEASUREMENT_ENVELOPE_ONLY"
scene["production_character_complete"] = False
scene["G1"] = "BLOCKED"
scene["G2"] = "NOT_RUN"
scene["G3"] = "ENVELOPE_GENERATED_ONLY"
scene["G4"] = "NOT_RUN"
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report = {
    "status": "PASS_NON_ANATOMICAL_ENVELOPE_GENERATION_ONLY",
    "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    "vertices": len(verts), "faces": len(faces), "rows": len(rows),
    "alpha_threshold": 224, "row_stride": 4, "segments": segments,
    "source_sha256": {d: index[n]["sha256"] for d, n in VIEWS.items()},
    "limitations": ["not anatomy", "not final character",
                    "front/back and left/right silhouette union",
                    "unverified physical dimensions",
                    "no costume, hair, accessories or rig"],
    "G1": "BLOCKED", "G2": "NOT_RUN",
    "G3": "GEOMETRY_GENERATED_NOT_VISUALLY_APPROVED", "G4": "NOT_RUN",
}
out.with_suffix(".json").write_text(json.dumps(report, indent=2))
print(json.dumps({"status": report["status"], "vertices": len(verts), "faces": len(faces)}))
