"""Generate a non-canonical, reviewable closed-eyelid curve from EYELID-05 measurements.

Pure Python, no Blender dependency. This is an art-target proposal only, not a shape key.
"""
import argparse
import json
import math
from pathlib import Path


def bernstein4(control, u):
    return sum(math.comb(4, k) * (u ** k) * ((1 - u) ** (4 - k)) * control[k]
               for k in range(5))


def build_target(source, samples=33, curvature_px=0.65):
    if samples < 5:
        raise ValueError("samples must be >= 5")
    if not 0 <= curvature_px <= 2:
        raise ValueError("curvature_px must be in [0, 2]")
    result = {"schema": "MORWEN-EYELID-06-CLOSED-CURVE-CANDIDATE",
              "status": "UNREVIEWED_ART_PROPOSAL_NOT_CANON",
              "source_sha256": source["source"]["sha256"],
              "coordinate_system": "image pixels; y increases downward",
              "curvature_px": curvature_px, "sides": {}}
    for side in ("R", "L"):
        upper = source["design_coef"][side]["upper_coef"]
        lower = source["design_coef"][side]["lower_coef"]
        if abs(upper[0] - lower[0]) > 1e-6 or abs(upper[-1] - lower[-1]) > 1e-6:
            raise ValueError("canthus endpoints differ")
        c = source["measured"][side]
        x0, x1 = c["canthus_inner_px"][0], c["canthus_outer_px"][0]
        points = []
        for i in range(samples):
            u = i / (samples - 1)
            y_top, y_bottom = bernstein4(upper, u), bernstein4(lower, u)
            if y_top > y_bottom + 1e-6:
                raise ValueError(f"crossed neutral margins at {side} u={u}")
            # Mid-gap is a candidate only; smooth arch is zero at both canthi.
            y = (y_top + y_bottom) / 2 - curvature_px * math.sin(math.pi * u)
            if i == 0:
                y = upper[0]
            if i == samples - 1:
                y = upper[-1]
            points.append({"u": round(u, 8), "x_px": round(x0 + (x1 - x0) * u, 6),
                           "y_px": round(y, 6)})
        result["sides"][side] = {"points": points, "neutral_inner_y_px": upper[0],
                                 "neutral_outer_y_px": upper[-1]}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--curvature-px", type=float, default=0.65)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    target = build_target(source, curvature_px=args.curvature_px)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(target, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
