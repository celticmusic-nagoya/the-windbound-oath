#!/usr/bin/env python3
"""Package actual Blender outputs into an auditable candidate handoff manifest.

Does not approve art, invent spatial metrics, or modify canonical source.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
SOURCE_COMMIT = "dc17dd4846f35ea1f5dea25168eec9ddb50a3838"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--blender-version", required=True)
    parser.add_argument("--generator-version", default="lind-source-review-v1")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    assert args.scene.is_file(), "missing Blender scene"
    assert args.reference.is_file(), "missing approved source"
    assert hashlib.sha256(args.reference.read_bytes()).hexdigest() == SOURCE_SHA, "reference SHA mismatch"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene_copy = args.output_dir / "source-review.blend"
    scene_copy.write_bytes(args.scene.read_bytes())
    manifest = {
        "schema_version": 1,
        "lane": "INTEGRATION",
        "collection": "LIND_STORY_MARKERS",
        "source_image_sha256": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "generator_version": args.generator_version,
        "blender_version": args.blender_version,
        "random_seed": args.seed,
        "art_status": "REFERENCE",
        "qa_status": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
        "metric_approval": "BLOCKED",
        "local_origin": None,
        "bounding_box_m": None,
        "world_transform": None,
        "elevation_reference": None,
        "input_hashes": {"approved_reference": SOURCE_SHA},
        "output_hashes": {"source-review.blend": hashlib.sha256(scene_copy.read_bytes()).hexdigest()},
        "dependencies": [],
        "exclusion_masks": [],
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("PACKAGED: source-review scene only; G2/G4 NOT_RUN")


if __name__ == "__main__":
    main()
