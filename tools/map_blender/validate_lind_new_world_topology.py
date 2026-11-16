#!/usr/bin/env python3
"""Validate the unscaled Rilde topology without relying on legacy map coordinates."""
import json
import pathlib
import sys

def validate(data):
    errors = []
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        errors.append("duplicate node id")
    required = {"village_center", "windward_cliffs_wnw", "raid_riverside_cliff", "harbor_sw", "north_farms", "road_to_dunvall", "east_river_bridge", "downstream_landing", "moss_forest", "ancient_altar"}
    if not required.issubset(set(ids)):
        errors.append("missing required canonical node")
    if any(value is not None for value in data.get("metric", {}).values()):
        errors.append("unapproved metric value")
    if data.get("source", {}).get("sha256") != "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620":
        errors.append("approved image source SHA mismatch")
    for e in edges:
        if e.get("from") not in ids or e.get("to") not in ids:
            errors.append("edge with missing endpoint")
    jumps = [e for e in edges if e.get("kind") == "story_jump"]
    if len(jumps) != 1 or jumps[0].get("from") != "raid_riverside_cliff" or jumps[0].get("to") != "downstream_landing" or jumps[0].get("bidirectional") is not False:
        errors.append("raid downstream story jump must be directed")
    if any(e.get("kind") == "story_jump" and ("windward_cliffs_wnw" in (e.get("from"),e.get("to"))) for e in edges):
        errors.append("coastal sunset cliff must not be raid jump")
    return errors

def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2] / "docs/production/lind-new-world-topology.v1.json"
    errors = validate(json.loads(path.read_text(encoding="utf-8")))
    if errors:
        print("FAIL: " + "; ".join(errors))
        return 1
    print("PASS: topology contract semantic checks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
