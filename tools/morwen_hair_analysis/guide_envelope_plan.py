"""Independent new-guide envelope planner (W121A).

Read-only.  Given the clean guide silhouette (from guide_support_v2) and the
blueprint lanes, it answers:
  * which lanes the current guide can host with the required inside depth;
  * for the remaining lanes, the lateral/vertical deficit per row band, i.e.
    how far a *new, independent* Freehand guide must extend;
  * a target 2D envelope (screen px and blueprint px) for that new guide.

The envelope is a 2D front-view requirement only.  It does not infer depth.
Converting it into VRoid guide control-point moves still needs measured GUI
response (repository precision playbook): plan -> move -> re-measure.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scipy import ndimage

from guide_support_v2 import (filled_silhouette, grid_spacing, guide_mask, lane_path,
                              load_rgb, sample, sha256, signed_distance)


def plan(reference_png, registration, blueprint, lanes, *, margin_px=1.0,
         uncertainty_px=1.0, band_px=8) -> dict:
    reg = json.loads(Path(registration).read_text())
    bp = json.loads(Path(blueprint).read_text())
    wire = guide_mask(load_rgb(reference_png))
    sp = grid_spacing(wire)
    sil = filled_silhouette(wire, int(math.ceil(sp / 2)) + 1)
    sdf = signed_distance(sil)
    need = margin_px + uncertainty_px
    s = reg["scale"] * 29 / 51
    cx, cy = reg["center_px"]
    host, new = [], []
    rows = {}
    for lane in lanes:
        p = lane_path(bp, lane, reg)
        d = [sample(sdf, x, y) for x, y in p]
        worst = max(d)
        (host if worst + need <= 0 else new).append(lane)
        for (x, y), v in zip(p, d):
            if v + need <= 0:
                continue
            yb = int(y // band_px * band_px)
            r = np.nonzero(sil[min(max(int(round(y)), 0), sil.shape[0] - 1)])[0]
            left_edge, right_edge = (int(r.min()), int(r.max())) if len(r) else (None, None)
            e = rows.setdefault(yb, dict(lanes=set(), left_deficit_px=0.0, right_deficit_px=0.0,
                                         no_guide_row_deficit_px=0.0, guide_row_extent_px=[left_edge, right_edge]))
            e["lanes"].add(lane)
            deficit = v + need
            if left_edge is None:
                e["no_guide_row_deficit_px"] = max(e["no_guide_row_deficit_px"], deficit)
            elif x < (left_edge + right_edge) / 2:
                e["left_deficit_px"] = max(e["left_deficit_px"], deficit)
            else:
                e["right_deficit_px"] = max(e["right_deficit_px"], deficit)
    # Target envelope for the new guide: union of the unhosted lane paths dilated by need+2 px.
    env = np.zeros_like(sil)
    for lane in new:
        for x, y in lane_path(bp, lane, reg):
            X, Y = int(round(x)), int(round(y))
            if 0 <= X < env.shape[1] and 0 <= Y < env.shape[0]:
                env[Y, X] = True
    env = ndimage.binary_dilation(env, iterations=int(math.ceil(need)) + 2)
    env = ndimage.binary_fill_holes(ndimage.binary_closing(env, iterations=3))
    ys, xs = np.nonzero(env)
    to_bp = lambda X, Y: [round((X - cx) / s + 212.5, 2), round((Y - cy) / s + 125, 2)]
    bands = []
    for yb in sorted(rows):
        e = rows[yb]
        bands.append(dict(y_band_px=[yb, yb + band_px - 1], lanes=sorted(e["lanes"]),
                          guide_row_extent_px=e["guide_row_extent_px"],
                          left_extension_px=round(e["left_deficit_px"], 2),
                          right_extension_px=round(e["right_deficit_px"], 2),
                          no_guide_row_px=round(e["no_guide_row_deficit_px"], 2)))
    out = dict(schema="morwen_new_guide_envelope_w121a",
               status="DESIGN_ONLY_2D_FRONT_REQUIREMENT",
               reference_sha256=sha256(reference_png), wire_grid_spacing_px=sp,
               required_inside_depth_px=need,
               current_guide_hosts=host, needs_independent_guide=new,
               bands=bands)
    if len(xs):
        out["new_guide_target_bounds_px"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        out["new_guide_target_bounds_blueprint_px"] = to_bp(xs.min(), ys.min()) + to_bp(xs.max(), ys.max())
        out["new_guide_target_area_px"] = int(env.sum())
    return out


def main(argv):
    ref, reg, bp, out, *lanes = argv
    res = plan(ref, reg, bp, lanes or ["F01", "F02", "F03", "F04", "F05", "F06"])
    with Path(out).open("x") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({"hosts": res["current_guide_hosts"], "new": res["needs_independent_guide"]}))


if __name__ == "__main__":
    main(sys.argv[1:])
