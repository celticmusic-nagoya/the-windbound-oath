"""Fail-closed structural audit for independent, provisional LIND cliff Blender assets.

Run inside Blender 5.2.4:
  blender -b asset.blend --python qa_provisional_cliff_asset.py -- --out qa.json

This audits an existing authored asset; it never creates geometry or claims G2/G4 PASS.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

REQUIRED = (
    "coordinate_space", "unit_scale_status", "origin_convention",
    "ground_contact_convention", "source_manifest_sha256",
    "source_license", "producer_commit",
)
def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def audit():
    scene = bpy.context.scene
    issues = []
    meta = {key: scene.get(key) for key in REQUIRED}
    for key in REQUIRED:
        if not isinstance(meta[key], str) or not meta[key].strip():
            issues.append("MISSING_SCENE_METADATA:" + key)
    if meta["coordinate_space"] != "asset-local-provisional":
        issues.append("INVALID_COORDINATE_SPACE")
    if meta["unit_scale_status"] != "UNAPPROVED":
        issues.append("WORLD_SCALE_MUST_REMAIN_UNAPPROVED")
    if scene.get("canonical_world_placement") not in (None, "BLOCKED_FOR_INTEGRATION"):
        issues.append("CANONICAL_PLACEMENT_NOT_BLOCKED")
    meshes = [o for o in scene.objects if o.type == "MESH" and not o.get("qa_exclude")]
    if not meshes:
        issues.append("NO_ASSET_MESH")
    report_meshes = []
    for obj in meshes:
        mesh = obj.data
        if not mesh.polygons:
            issues.append("EMPTY_MESH:" + obj.name)
        if any(abs(v) < 1e-10 for v in obj.scale):
            issues.append("DEGENERATE_OBJECT_SCALE:" + obj.name)
        if not mesh.uv_layers:
            issues.append("MISSING_UV:" + obj.name)
        report_meshes.append({
            "name": obj.name,
            "vertices": len(mesh.vertices),
            "polygons": len(mesh.polygons),
            "uv_layers": len(mesh.uv_layers),
            "material_slots": len(obj.material_slots),
            "local_bounds": [list(v) for v in obj.bound_box],
            "transform": [list(row) for row in obj.matrix_world],
        })
    missing_images = sorted({
        str(img.filepath) for img in bpy.data.images
        if img.source == "FILE" and not img.packed_file and
        not (bpy.path.abspath(img.filepath) and Path(bpy.path.abspath(img.filepath)).exists())
    })
    if missing_images:
        issues.append("MISSING_EXTERNAL_TEXTURES")
    source = Path(bpy.data.filepath) if bpy.data.filepath else None
    if source is None or not source.is_file():
        issues.append("UNSAVED_OR_MISSING_BLEND")
    return {
        "schema": "two-provisional-cliff-local-qa-v1",
        "blender_version": bpy.app.version_string,
        "source_blend": str(source) if source else None,
        "source_blend_sha256": digest(source) if source and source.is_file() else None,
        "metadata": meta,
        "mesh_inventory": report_meshes,
        "missing_external_textures": missing_images,
        "structural_preflight": "PASS" if not issues else "FAIL",
        "issues": issues,
        "G1": "NOT_RUN",
        "G2": "NOT_RUN",
        "G3": "NOT_RUN",
        "G4": "NOT_RUN",
        "integration": "BLOCKED_FOR_INTEGRATION",
        "note": "Preflight PASS is not a G3 PASS; independent render/topology/UV review required.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    report = audit()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TWO_LIND_LOCAL_QA_" + report["structural_preflight"], flush=True)
    if report["issues"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
