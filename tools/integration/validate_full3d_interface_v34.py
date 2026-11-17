#!/usr/bin/env python3
"""Fail-closed validation of proposed cross-lane full-3D manifests (stdlib only).

This is NOT a Blender/art/runtime QA tool and cannot approve canon or metrics.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

STATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
LANES = {"CHARACTER", "WORLD", "HOME", "BUILD", "ECO", "INTEGRATION"}
WORLD_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
CHARACTER_REFERENCES = {
    "47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638",
    "d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b",
}
COLLECTION_OWNERS = {
    "LIND_TERRAIN": "WORLD", "LIND_WATER": "WORLD",
    "LIND_ROADS": "WORLD", "LIND_HERO_HOME": "HOME",
    "LIND_BUILDINGS": "BUILD", "LIND_ECOLOGY": "ECO",
    "LIND_STORY_MARKERS": "INTEGRATION",
}
UNAPPROVED_FIELDS = (
    "local_origin", "world_transform", "bounds", "projection_id",
    "ground_contact", "shadow_anchor", "occlusion_contract",
    "collision_contract", "animation_state_map", "runtime_budget_ref",
)
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def safe_artifact_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    p = PurePosixPath(relative)
    if p.is_absolute() or any(x in ("", ".", "..") for x in relative.split("/")):
        return None
    resolved_root = root.resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(resolved_root):
        return None
    return target


def validate(data, root):
    errors = []
    def need(ok, reason):
        if not ok:
            errors.append(reason)

    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]
    need(data.get("contract_version") == "v3.4-candidate-1", "unsupported contract_version")
    lane = data.get("lane")
    need(lane in LANES, "unknown lane")
    need(isinstance(data.get("asset_id"), str) and bool(data.get("asset_id")), "asset_id missing")
    need(data.get("status") in {"reference", "candidate", "approved"}, "invalid status")
    need(data.get("status") != "approved", "this candidate validator cannot authorize adopted assets")
    need(isinstance(data.get("source_commit"), str) and bool(COMMIT.fullmatch(data["source_commit"])), "invalid source_commit")
    need(isinstance(data.get("blender_version"), str) and bool(data.get("blender_version")), "blender_version missing")
    need(isinstance(data.get("generator_version"), str) and bool(data.get("generator_version")), "generator_version missing")
    need(type(data.get("seed")) is int or data.get("seed") == "not_applicable", "seed invalid")
    need(isinstance(data.get("license_provenance"), list), "license_provenance must be a list")
    need(isinstance(data.get("dependencies_on_lanes"), list), "dependencies_on_lanes must be a list")
    for key in ("dependencies", "camera_settings", "render_settings"):
        need(isinstance(data.get(key), dict), key + " must be an object")

    sources = data.get("source_hashes")
    need(isinstance(sources, dict) and bool(sources), "source_hashes must be nonempty object")
    if isinstance(sources, dict):
        for name, digest in sources.items():
            need(isinstance(name, str) and bool(name) and isinstance(digest, str) and bool(SHA.fullmatch(digest)), "invalid source hash")
        if lane in {"WORLD", "HOME", "BUILD", "ECO"}:
            need(WORLD_SHA in sources.values(), "WORLD source SHA absent")
            need(not any(x in CHARACTER_REFERENCES for x in sources.values()), "character SHA used in MAP manifest")
        if lane == "CHARACTER":
            need(WORLD_SHA not in sources.values(), "WORLD SHA used in CHARACTER manifest")
            need(not any(x in CHARACTER_REFERENCES for x in sources.values()) or data.get("canon_precedence") == "BLOCKED", "character reference precedence not reconciled")

    collection = data.get("collection")
    if lane in {"WORLD", "HOME", "BUILD", "ECO"}:
        need(COLLECTION_OWNERS.get(collection) == lane, "collection owner mismatch")
    elif collection is not None:
        need(COLLECTION_OWNERS.get(collection) == lane, "cross-lane collection ownership")

    approval = data.get("interface_approval")
    need(approval == "BLOCKED", "candidate-only validator cannot certify interface approval")
    if approval != "APPROVED":
        for field in UNAPPROVED_FIELDS:
            need(field in data and data[field] is None, field + " must be explicit null before approval")

    gates = data.get("qa_gates")
    need(isinstance(gates, dict) and set(gates) == {"G1", "G2", "G3", "G4"}, "G1-G4 required")
    if isinstance(gates, dict):
        need(all(v in STATES for v in gates.values()), "invalid QA gate status")
        need(gates.get("G1") != "PASS" or approval == "APPROVED", "G1 PASS requires approved interface")
        need(gates.get("G2") != "PASS", "G2 art PASS cannot be asserted by this candidate validator")
        need(gates.get("G4") != "PASS", "G4 device PASS cannot be asserted by this candidate validator")

    outputs = data.get("output_hashes")
    need(isinstance(outputs, dict), "output_hashes must be object")
    if isinstance(outputs, dict):
        for relative, digest in outputs.items():
            target = safe_artifact_path(root, relative)
            need(target is not None, "unsafe artifact path")
            need(isinstance(digest, str) and bool(SHA.fullmatch(digest)), "invalid output SHA")
            if target is not None:
                need(target.is_file(), "missing output artifact: " + relative)
                if target.is_file() and isinstance(digest, str):
                    need(hashlib.sha256(target.read_bytes()).hexdigest() == digest, "output SHA mismatch: " + relative)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        errors = validate(data, args.manifest.parent)
    except (OSError, ValueError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("PASS: candidate interface manifest structure and local hashes only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
