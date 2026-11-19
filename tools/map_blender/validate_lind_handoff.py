#!/usr/bin/env python3
"""Fail-closed, Blender-independent validator for cross-agent production manifests."""
import argparse
import hashlib
import json
import pathlib
import sys

SOURCE_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
LANES = {"WORLD", "HOME", "BUILD", "ECO", "INTEGRATION", "QA"}
COLLECTIONS = {
    "LIND_TERRAIN": "WORLD", "LIND_WATER": "WORLD",
    "LIND_ROADS": "WORLD", "LIND_HERO_HOME": "HOME",
    "LIND_BUILDINGS": "BUILD", "LIND_ECOLOGY": "ECO",
    "LIND_STORY_MARKERS": "INTEGRATION",
}
STATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
STATUSES = {"CANDIDATE", "REFERENCE", "ADOPTED"}
NULL_METRICS = ("local_origin", "bounding_box_m", "world_transform", "elevation_reference")


def validate(data, root):
    errors = []
    def require(ok, msg):
        if not ok:
            errors.append(msg)
    require(data.get("schema_version") == 1, "schema_version must be 1")
    lane = data.get("lane")
    require(lane in LANES, "unknown lane")
    require(data.get("source_image_sha256") == SOURCE_SHA, "source image SHA mismatch")
    require(isinstance(data.get("generator_version"), str) and bool(data.get("generator_version")), "generator_version missing")
    require(isinstance(data.get("blender_version"), str) and bool(data.get("blender_version")), "blender_version missing")
    require(type(data.get("random_seed")) is int, "random_seed must be integer")
    require(data.get("art_status") in STATUSES, "invalid art_status")
    qa = data.get("qa_status")
    require(isinstance(qa, dict) and set(qa) == {"G1", "G2", "G3", "G4"}, "four QA gates required")
    if isinstance(qa, dict):
        require(all(x in STATES for x in qa.values()), "invalid QA state")
        require(not (qa.get("G1") == "PASS" and data.get("metric_approval") != "APPROVED"), "G1 cannot PASS without metric approval")
    require(data.get("metric_approval") in {"BLOCKED", "APPROVED"}, "metric approval must be explicit")
    if data.get("metric_approval") != "APPROVED":
        for key in NULL_METRICS:
            require(data.get(key, "MISSING") is None, key + " must be null before metric approval")
    collection = data.get("collection")
    require(collection in COLLECTIONS, "unknown collection")
    if collection in COLLECTIONS:
        require(COLLECTIONS[collection] == lane, "collection owner mismatch")
    require(data.get("source_commit") == "dc17dd4846f35ea1f5dea25168eec9ddb50a3838", "source commit mismatch")
    require(isinstance(data.get("dependencies"), list), "dependencies must be a list")
    require(isinstance(data.get("exclusion_masks"), list), "exclusion_masks must be a list")
    hashes = data.get("output_hashes")
    require(isinstance(hashes, dict), "output_hashes must be an object")
    if isinstance(hashes, dict):
        for relative, expected in hashes.items():
            require(isinstance(relative, str) and relative and not pathlib.PurePosixPath(relative).is_absolute() and ".." not in pathlib.PurePosixPath(relative).parts, "unsafe artifact path")
            require(isinstance(expected, str) and len(expected) == 64 and all(c in "0123456789abcdef" for c in expected), "invalid artifact SHA")
            if isinstance(relative, str) and relative and not pathlib.PurePosixPath(relative).is_absolute() and ".." not in pathlib.PurePosixPath(relative).parts and isinstance(expected, str):
                path = root / relative
                require(path.is_file(), "missing artifact: " + relative)
                if path.is_file():
                    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "artifact SHA mismatch: " + relative)
    require(isinstance(data.get("input_hashes"), dict), "input_hashes must be an object")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=pathlib.Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(data, args.manifest.parent)
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("PASS: cross-agent Blender handoff manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
