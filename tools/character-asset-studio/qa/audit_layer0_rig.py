#!/usr/bin/env python3
"""Read-only QA for Morwen candidate rigs. No image or canonical file mutation."""
import argparse
import json
from pathlib import Path


def audit(spec):
    checks = []
    joints = spec.get("joints3d", {})
    tree = spec.get("kinematicTree", {})
    def check(name, passed, detail):
        checks.append({"id": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    check("canvas", spec.get("canvas") == {"width": 1200, "height": 1600},
          spec.get("canvas"))
    check("ground_anchor", spec.get("anchor", {}).get("px") == [600, 1540],
          spec.get("anchor", {}).get("px"))
    check("joint_parent_refs", all(k in joints and p in joints for k, p in tree.items()),
          {"jointCount": len(joints), "parentLinks": len(tree)})
    check("single_deform_root", set(joints) - set(tree) == {"pelvis"},
          sorted(set(joints) - set(tree)))

    cycles = []
    for joint in joints:
        seen = set()
        cur = joint
        while cur in tree:
            if cur in seen:
                cycles.append(joint)
                break
            seen.add(cur)
            cur = tree[cur]
    check("acyclic", not cycles, cycles)

    symmetry_errors = []
    for name, pos in joints.items():
        if name.endswith("L"):
            other = joints.get(name[:-1] + "R")
            if other is None or len(pos) != 3 or len(other) != 3 or (
                pos[0] != -other[0] or pos[1:] != other[1:]
            ):
                symmetry_errors.append(name)
    check("paired_joint_mirror", not symmetry_errors, symmetry_errors)

    # A planted world-space reference must not inherit pelvis transforms.
    check("ground_not_deform_child", "ground" not in tree,
          {"groundParent": tree.get("ground")})

    # Age migration is an explicit candidate metadata gate, not a retroactive edit.
    check("current_age_metadata", spec.get("ageCategory") == "adult",
          {"ageCategory": spec.get("ageCategory"),
           "bodyGuidePolicy": spec.get("bodyGuidePolicy")})

    return {
        "schema": "cas/independent-rig-audit/1.0",
        "readOnly": True,
        "adoptionReady": False,
        "checks": checks,
        "summary": {
            "pass": sum(x["status"] == "PASS" for x in checks),
            "fail": sum(x["status"] == "FAIL" for x in checks)
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.candidate_json.read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if result["summary"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
