"""Post-stroke completion audit for VRoid freehand strands (independent analysis, W121A).

Read-only.  Compares the screenshot before a stroke with the one after it and
measures how much of the designed lane path actually received new pixels.
A stroke whose path leaves the guide surface is silently truncated by the
editor; the label "Hair N" still appears, so a label-only guard passes.

Noise gate: an invariant region (default jacket block) must be pixel-identical
between both frames, otherwise the result is HOLD (camera/pose/animation drift).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guide_support_v2 import lane_path, load_rgb, sha256

INVARIANT = (450, 450, 575, 560)  # x0, y0, x1, y1 jacket block used by W110 registration


def audit(before_png, after_png, registration, blueprint, lane, *, window=3,
          change_threshold=40, min_completion=0.9, invariant=INVARIANT) -> dict:
    a = load_rgb(before_png)
    b = load_rgb(after_png)
    reg = json.loads(Path(registration).read_text())
    bp = json.loads(Path(blueprint).read_text())
    x0, y0, x1, y1 = invariant
    noise = int(np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).max())
    path = lane_path(bp, lane, reg)
    prof = []
    for x, y in path:
        X, Y = round(x), round(y)
        w = np.abs(a[Y - window:Y + window + 1, X - window:X + window + 1]
                   - b[Y - window:Y + window + 1, X - window:X + window + 1]).max(2)
        prof.append(int(w.max()))
    hit = [v > change_threshold for v in prof]
    # Contiguous drawn run from the root side (allow the very first two samples to be
    # under the root cap).  Completion = last contiguous changed sample / path length.
    start = next((i for i, h in enumerate(hit) if h), None)
    if start is None:
        last = -1
    else:
        last = start
        while last + 1 < len(hit) and hit[last + 1]:
            last += 1
    completion = (last + 1) / len(path) if last >= 0 else 0.0
    if noise > 0:
        verdict = "HOLD_FRAME_DRIFT"
    elif start is None:
        verdict = "NOT_DRAWN"
    elif start > 2:
        verdict = "ROOT_GAP"
    elif completion >= min_completion:
        verdict = "COMPLETE"
    else:
        verdict = "TRUNCATED"
    return dict(schema="morwen_stroke_completion_w121a", lane=lane,
                before_sha256=sha256(before_png), after_sha256=sha256(after_png),
                invariant_region_max_diff=noise, points=len(path), first_drawn_index=start,
                last_contiguous_index=last, completion_fraction=round(completion, 4),
                min_completion=min_completion, verdict=verdict, per_point_max_diff=prof,
                limitation="2D screen change along designed path; not a 3D length or width measurement")


def main(argv):
    before, after, reg, bp, lane, out = argv
    res = audit(before, after, reg, bp, lane)
    with Path(out).open("x") as f:
        json.dump(res, f, indent=2)
    print(res["verdict"], res["completion_fraction"])


if __name__ == "__main__":
    main(sys.argv[1:])
