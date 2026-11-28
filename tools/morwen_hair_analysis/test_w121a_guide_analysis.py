"""Credential-free synthetic tests for W121A guide analysis (no private data).

Run: python3 tools/morwen_hair_analysis/test_w121a_guide_analysis.py
Each test has a positive and a negative control so a broken metric cannot pass.
"""
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guide_envelope_plan as gep  # noqa: E402
import guide_support_v2 as gs  # noqa: E402
import stroke_completion_audit as sca  # noqa: E402

BG = (232, 232, 232)
WIRE = (194, 217, 65)
STRAND = (90, 60, 100)
JACKET = (30, 35, 60)
REG = {"center_px": [511.5, 385.5], "scale": 1.28}
S = REG["scale"] * 29 / 51


def to_bp(x, y):
    return [(x - REG["center_px"][0]) / S + 212.5, (y - REG["center_px"][1]) / S + 125]


def guide_wire(img, cx=511.5, cy=370, rx=30, ry=55, step=6, dx=0, k=1.0):
    a = np.asarray(img).copy()
    yy, xx = np.mgrid[0:768, 0:1024]
    inside = ((xx - (cx + dx)) / (rx * k)) ** 2 + ((yy - cy) / (ry * k)) ** 2 <= 1
    grid = ((np.rint((xx - (cx + dx)) / k).astype(int) % step == 0) | (np.rint((yy - cy) / k).astype(int) % step == 0))
    a[inside & grid] = WIRE
    return Image.fromarray(a)


def base():
    a = np.full((768, 1024, 3), BG, np.uint8)
    a[450:560, 450:575] = JACKET
    a[470:480, 500:520] = (200, 200, 210)  # jacket detail
    return Image.fromarray(a)


def blueprint(tmp):
    lanes = {
        # inside: vertical line through the guide centre
        "IN": [to_bp(511.5, 335), to_bp(511.5, 350), to_bp(511.5, 365), to_bp(511.5, 380)],
        # outside: hugging the right edge, 5 px outside the ellipse at mid height
        "OUT": [to_bp(535, 335), to_bp(543, 352), to_bp(546, 368), to_bp(546, 384)],
    }
    d = {"schema": "synthetic", "view_lanes": {"front": [{"id": k, "points_px": v} for k, v in lanes.items()]}}
    p = Path(tmp) / "bp.json"
    p.write_text(json.dumps(d))
    return p


def save(img, tmp, name):
    p = Path(tmp) / name
    img.save(p)
    return p


def reg_file(tmp, name, reg):
    p = Path(tmp) / name
    p.write_text(json.dumps(reg))
    return p


def occlude(img, box):
    a = np.asarray(img).copy()
    x0, y0, x1, y1 = box
    a[y0:y1, x0:x1] = STRAND
    return Image.fromarray(a)


def test_occlusion_invariance_and_legacy_degradation(tmp):
    bp = blueprint(tmp)
    r = reg_file(tmp, "r.json", REG)
    clean = save(guide_wire(base()), tmp, "clean.png")
    occl = save(occlude(guide_wire(base()), (523, 330, 545, 390)), tmp, "occl.png")
    a = gs.analyse(clean, r, clean, r, bp, ["IN", "OUT"])
    b = gs.analyse(clean, r, occl, r, bp, ["IN", "OUT"])
    assert a["guide_geometry"] == b["guide_geometry"] == "UNCHANGED"
    assert a["lanes"]["IN"]["verdict"] == b["lanes"]["IN"]["verdict"] == "PASS"
    assert a["lanes"]["OUT"]["verdict"] == b["lanes"]["OUT"]["verdict"] == "OUTSIDE"
    assert a["lanes"]["OUT"]["worst_signed_distance_px"] == b["lanes"]["OUT"]["worst_signed_distance_px"]
    # negative control: the legacy wire-distance metric must degrade under occlusion
    assert b["lanes"]["OUT"]["legacy_max_chebyshev_px"] > a["lanes"]["OUT"]["legacy_max_chebyshev_px"]
    assert b["visible_fraction"] < a["visible_fraction"] == 1.0


def test_moved_guide_fails_closed(tmp):
    bp = blueprint(tmp)
    r = reg_file(tmp, "r.json", REG)
    clean = save(guide_wire(base()), tmp, "clean.png")
    moved = save(guide_wire(base(), dx=9), tmp, "moved.png")
    res = gs.analyse(clean, r, moved, r, bp, ["IN"])
    assert res["guide_geometry"] == "MOVED_OR_NEW_GUIDE"
    assert res["lanes"]["IN"]["verdict"] == "HOLD_GUIDE_GEOMETRY"


def test_scaled_camera_registration(tmp):
    bp = blueprint(tmp)
    r = reg_file(tmp, "r.json", REG)
    k = 0.9
    live_reg = {"center_px": [511.5, 385.5 + 2], "scale": REG["scale"] * k}
    lr = reg_file(tmp, "lr.json", live_reg)
    clean = save(guide_wire(base()), tmp, "clean.png")
    cy = 385.5 + 2 + (370 - 385.5) * k
    live = save(guide_wire(base(), cy=cy, rx=30 * k, ry=55 * k, step=6, k=k), tmp, "live.png")
    res = gs.analyse(clean, r, live, lr, bp, ["IN"])
    assert res["guide_geometry"] == "UNCHANGED", res["stray_live_wire_px"]
    assert res["lanes"]["IN"]["verdict"] == "PASS"
    # negative control: wrong registration (no scale) must not look unchanged
    bad = gs.analyse(clean, r, live, r, bp, ["IN"])
    assert bad["guide_geometry"] == "MOVED_OR_NEW_GUIDE"


def stroke(img, path, upto):
    a = np.asarray(img).copy()
    n = max(1, int(len(path) * upto))
    for x, y in path[:n]:
        X, Y = round(x), round(y)
        a[Y - 2:Y + 3, X - 2:X + 3] = STRAND
    return Image.fromarray(a)


def test_completion_audit(tmp):
    bp = blueprint(tmp)
    r = reg_file(tmp, "r.json", REG)
    path = gs.lane_path(json.loads(bp.read_text()), "IN", REG)
    before = guide_wire(base())
    b = save(before, tmp, "b.png")
    full = save(stroke(before, path, 1.0), tmp, "full.png")
    half = save(stroke(before, path, 0.5), tmp, "half.png")
    assert sca.audit(b, full, r, bp, "IN")["verdict"] == "COMPLETE"
    h = sca.audit(b, half, r, bp, "IN")
    assert h["verdict"] == "TRUNCATED" and 0.4 < h["completion_fraction"] < 0.65
    assert sca.audit(b, b, r, bp, "IN")["verdict"] == "NOT_DRAWN"
    drift = np.asarray(Image.open(full)).copy()
    drift[500, 500] = (0, 0, 0)
    d = save(Image.fromarray(drift), tmp, "drift.png")
    assert sca.audit(b, d, r, bp, "IN")["verdict"] == "HOLD_FRAME_DRIFT"


def test_envelope_plan(tmp):
    bp = blueprint(tmp)
    r = reg_file(tmp, "r.json", REG)
    clean = save(guide_wire(base()), tmp, "clean.png")
    plan = gep.plan(clean, r, bp, ["IN", "OUT"])
    assert plan["current_guide_hosts"] == ["IN"] and plan["needs_independent_guide"] == ["OUT"]
    right = max(b["right_extension_px"] for b in plan["bands"])
    left = max(b["left_extension_px"] for b in plan["bands"])
    assert right > 3 and left == 0, (left, right)
    x0, y0, x1, y1 = plan["new_guide_target_bounds_px"]
    assert x1 > 541.5 and x0 > 511.5


def main():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        with tempfile.TemporaryDirectory() as tmp:
            t(tmp)
        print("PASS", t.__name__)
    print(f"{len(tests)}/{len(tests)} PASS")


if __name__ == "__main__":
    main()
