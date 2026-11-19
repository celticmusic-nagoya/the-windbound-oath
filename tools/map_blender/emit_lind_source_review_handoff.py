#!/usr/bin/env python3
"""Emit a verified source-review Blender artifact manifest (never a terrain art PASS).

Run inside Blender after reopening the generated .blend. Output hashes are
computed from actual saved bytes, not declared outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bpy

SOURCE_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
SOURCE_COMMIT = "dc17dd4846f35ea1f5dea25168eec9ddb50a3838"
COLLECTIONS = (
    "LIND_TERRAIN", "LIND_WATER", "LIND_ROADS", "LIND_HERO_HOME",
    "LIND_BUILDINGS", "LIND_ECOLOGY", "LIND_STORY_MARKERS",
)


def main():
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    path = Path(bpy.data.filepath).resolve()
    if not path.is_file():
        raise RuntimeError("Saved .blend is required")
    scene = bpy.context.scene
    if scene.get("approved_source_sha256") != SOURCE_SHA:
        raise RuntimeError("Approved source SHA mismatch")
    if scene.get("metric_approval") != "BLOCKED":
        raise RuntimeError("Source-review scene unexpectedly claims metric approval")
    if any(name not in bpy.data.collections for name in COLLECTIONS):
        raise RuntimeError("Missing named Blender production collection")
    markers = [obj for obj in bpy.data.objects if obj.name.startswith("SEMANTIC_")]
    if len(markers) != 11 or any(obj.type != "EMPTY" for obj in markers):
        raise RuntimeError("Source-review semantic marker contract violated")
    if any(obj.type == "MESH" for obj in bpy.data.objects):
        raise RuntimeError("Source-review must not masquerade as generated terrain")
    references = [im for im in bpy.data.images if im.get("role") == "APPROVED_VISUAL_REFERENCE_NOT_METRIC"]
    if len(references) != 1 or not references[0].packed_file:
        raise RuntimeError("Missing packed approved reference")
    packed = references[0].packed_file.data
    if hashlib.sha256(packed).hexdigest() != SOURCE_SHA:
        raise RuntimeError("Packed source bytes mismatch")

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.parent != path.parent:
        raise RuntimeError("Manifest must share directory with .blend")
    manifest = {
        "schema_version": 1,
        "lane": "INTEGRATION",
        "collection": "LIND_STORY_MARKERS",
        "source_image_sha256": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "generator_version": "source-review-1",
        "blender_version": bpy.app.version_string,
        "random_seed": 0,
        "art_status": "REFERENCE",
        "qa_status": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "PASS", "G4": "NOT_RUN"},
        "metric_approval": "BLOCKED",
        "local_origin": None, "bounding_box_m": None,
        "world_transform": None, "elevation_reference": None,
        "input_hashes": {"approved_visual_reference": SOURCE_SHA},
        "output_hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()},
        "dependencies": [],
        "exclusion_masks": [],
        "evidence": {
            "type": "SOURCE_REVIEW_ONLY_NO_TERRAIN",
            "semantic_markers": len(markers),
            "collections": list(COLLECTIONS),
            "packed_reference_sha256": SOURCE_SHA,
        },
    }
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PASS: reopened .blend and verified packed source; wrote", output)


if __name__ == "__main__":
    main()
