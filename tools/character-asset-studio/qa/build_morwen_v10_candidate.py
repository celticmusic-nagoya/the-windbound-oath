#!/usr/bin/env python3
"""Build an immutable v1.0 Morwen candidate from v0.9 without editing source files."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def build(source):
    result = copy.deepcopy(source)
    if source.get("version") != "0.9-articulated":
        raise ValueError("expected v0.9 candidate")
    if source.get("anchor", {}).get("px") != [600, 1540]:
        raise ValueError("unexpected canonical ground anchor")
    if source.get("kinematicTree", {}).get("ground") != "pelvis":
        raise ValueError("unexpected v0.9 hierarchy; manual review required")
    if source.get("status") not in ("UNAPPROVED_CANDIDATE", "candidate_not_canonical"):
        raise ValueError("refusing to migrate non-candidate source")

    # Preserve all deformable joints and their coordinates; remove ground from
    # the deforming hierarchy. Keep the original ground coordinate as a marker.
    del result["kinematicTree"]["ground"]
    result["worldAnchors"] = {
        "ground": {"px": [600, 1540], "space": "world", "followsRig": False}
    }
    result["ageYears"] = 18
    result["ageCategory"] = "adult"
    result["bodyGuidePolicy"] = "adult_neutral_structure"
    result["version"] = "1.0"
    result["status"] = "UNAPPROVED_CANDIDATE"
    result["finalAdoption"] = "NOT_RUN"
    result["migration"] = {
        "fromVersion": "0.9",
        "changedJointCoordinates": [],
        "removedParentLinks": ["ground->pelvis"],
        "preservedHistoricalEvidence": True,
        "note": "Age metadata update does not itself approve or change proportions."
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("source and output must differ")
    if args.output.exists():
        parser.error("output exists; refusing overwrite")
    raw = args.source.read_bytes()
    candidate = build(json.loads(raw))
    candidate["migration"]["sourceSha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sourceSha256": candidate["migration"]["sourceSha256"],
                      "status": candidate["status"]}))


if __name__ == "__main__":
    main()
