"""Validate four independently rendered Morwen candidate PNGs, fail closed.

This checks technical evidence ONLY; never awards G1/G2/G4 PASS.
Usage: python tools/character_blender/verify_morwen_four_views.py qa_lanes/render
"""
import hashlib
import json
import pathlib
import sys

DIRECTIONS = ("front", "back", "facing_right", "facing_left")
PREFIX = "MORWEN_QA_"
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(folder):
    root = pathlib.Path(folder)
    path = root / "MORWEN_FOUR_VIEW_REPORT.json"
    errors = []
    if not path.is_file():
        return {"status": "BLOCKED", "errors": ["missing report"], "art_qa": "NOT_RUN"}
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        return {"status": "BLOCKED", "errors": ["invalid report: " + str(exc)], "art_qa": "NOT_RUN"}
    if report.get("status") != "PASS_FOUR_RENDER_FILES_ONLY":
        errors.append("render report not successful")
    if not report.get("source_unchanged") or report.get("source_sha256") != report.get("source_sha256_after"):
        errors.append("source mutation or missing before/after hash")
    if report.get("canonical_design_match") != "BLOCKED" or report.get("artistic_qa") != "NOT_RUN":
        errors.append("report must not claim canonical/art approval")
    views = report.get("views")
    if not isinstance(views, list) or len(views) != 4:
        errors.append("expected exactly four views")
        views = []
    found = set()
    for view in views:
        if not isinstance(view, dict):
            errors.append("invalid view entry"); continue
        direction = view.get("direction")
        if direction not in DIRECTIONS or direction in found:
            errors.append("invalid/duplicate direction"); continue
        found.add(direction)
        filename = PREFIX + direction.upper() + ".png"
        if view.get("filename") != filename:
            errors.append("unexpected filename for " + direction); continue
        image = root / filename
        if not image.is_file():
            errors.append("missing " + filename); continue
        raw = image.read_bytes()
        if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) < 24:
            errors.append("not PNG " + filename); continue
        width = int.from_bytes(raw[16:20], "big")
        height = int.from_bytes(raw[20:24], "big")
        if (width, height) != (512, 768):
            errors.append("incorrect dimensions " + filename)
        if sha(image) != view.get("sha256") or len(raw) != view.get("bytes"):
            errors.append("hash/size mismatch " + filename)
        if view.get("status") != "RENDERED_NOT_ART_REVIEWED":
            errors.append("invalid review state " + filename)
    if found != set(DIRECTIONS):
        errors.append("incomplete directional set")
    return {"status": "PASS_FOUR_FILES_ONLY" if not errors else "BLOCKED",
            "errors": errors, "art_qa": "NOT_RUN", "canonical_design_match": "BLOCKED",
            "game_qa": "NOT_RUN"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_morwen_four_views.py <render_dir>")
    result = verify(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["status"] == "PASS_FOUR_FILES_ONLY" else 1)
