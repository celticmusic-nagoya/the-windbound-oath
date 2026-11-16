#!/usr/bin/env python3
"""Fail-closed preflight for Morwen 3D FRONT-ONLY candidate. Stdlib only."""
import argparse, json, pathlib, sys

REQUIRED = {"front"}
BANNED = {"back", "rear", "left", "right", "profile", "side", "turnaround", "sheet", "collage", "multi-view", "four-view"}
EXHAUSTED = "unconstrained-composite-image-generation"
SOURCE_HASH = "d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b"

def validate(spec):
    errors = []
    if spec.get("method_family") == EXHAUSTED:
        errors.append("STOP: exhausted composite-generation method (>=2 failures); cannot retry")
    if spec.get("view") != "front" or spec.get("views") != ["front"]:
        errors.append("FRONT_ONLY: exactly one front view required")
    if spec.get("output_count") != 1 or spec.get("layout") != "single_character":
        errors.append("SINGLE_IMAGE: no collage, multi-view or detail panels")
    if spec.get("canonical_design_sha256") != SOURCE_HASH:
        errors.append("CANONICAL: design sheet hash mismatch")
    if not 7.5 <= spec.get("target_heads", 0) <= 8.0:
        errors.append("PROPORTION: target must be 7.5-8 heads")
    if spec.get("garter_leg") != "anatomical_right":
        errors.append("GAR TER: anatomical right leg required")
    if spec.get("garter_front_screen_side") != "left":
        errors.append("GAR TER: front screen-left required")
    if not spec.get("landmarks_reviewed_by_artist"):
        errors.append("LANDMARKS: shoulder, bust, waist, crotch, knee, ankle, floor not reviewed")
    if not spec.get("independent_art_qa_required"):
        errors.append("ART_QA: independent review cannot be skipped")
    prompt = spec.get("prompt", "").lower()
    if any(token in prompt for token in BANNED):
        errors.append("PROMPT: prohibited multi-view/layout words detected")
    if "front" not in prompt:
        errors.append("PROMPT: front-only instruction missing")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=pathlib.Path)
    args = ap.parse_args()
    data = json.loads(args.spec.read_text(encoding="utf-8"))
    errors = validate(data)
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
