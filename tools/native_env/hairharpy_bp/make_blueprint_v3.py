#!/usr/bin/env python3
"""Generate qual_hair_blueprint_v3.json from v2: top cover layer, hanging/bang roots moved under the crown edge,
alternating radial layers, and a per-lock design registry (arc length, curvature distribution, width/thickness at
root/mid/tip, taper, section aspect) computed from the design spine itself (no 2D inference)."""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hh_volume as V  # noqa: E402

CROWN_EDGE_ELEV = 58.8  # measured: HairHarpy crown cap lower edge z = 0.1009 m on the 0.118 m head (run 45084619143)


def kappa(p0, p1, p2):
    a, b, c = math.dist(p0, p1), math.dist(p1, p2), math.dist(p0, p2)
    s = (a + b + c) / 2
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    return 0.0 if a * b * c == 0 else 4 * area / (a * b * c)


def design_spine(ax, lk):
    c = {"len": 0.0, "w": 1.0, "t": 1.0, "bend": lk["bend"], "lat": 0.0, "root": 0.0, "layer": lk.get("layer", 0.0)}
    V.STATIONS = 80
    sp = V.resample(V.spine(ax, lk, c), 40)
    return [V.add(s, n, lk["clear"] + c["layer"] + V.profile(lk["thickness"], u) / 2) for s, n, u in sp]


def registry(ax, lk):
    pts = design_spine(ax, lk)
    n = len(pts) - 1
    L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    k = {f"kappa_{int(u * 100):02d}": kappa(pts[int(u * n) - 2], pts[int(u * n)], pts[int(u * n) + 2]) for u in (0.25, 0.5, 0.75)}
    w = {f"width_{tag}": V.profile(lk["width"], u) for tag, u in (("root", 0.1), ("mid", 0.5), ("tip", 0.85))}
    t = {f"thickness_{tag}": V.profile(lk["thickness"], u) for tag, u in (("root", 0.1), ("mid", 0.5), ("tip", 0.85))}
    r = {"arc_length_spine": L, **k, **w, **t, "taper_085": w["width_tip"] / w["width_mid"],
         "section_aspect_mid": t["thickness_mid"] / w["width_mid"]}
    return {key: round(v, 6) for key, v in r.items()}


def main():
    v2 = json.loads((HERE / "qual_hair_blueprint_v2.json").read_text())
    bp = json.loads(json.dumps(v2))
    bp["blueprint_id"] = "QUAL-HH-VOLUME-V3"
    bp["schema"] = "two-hair-blueprint/v3"
    layer_toggle = {}
    for i, lk in enumerate(bp["locks"]):
        if lk["role"] in ("side", "back", "face_frame"):
            lk["root"]["elev"] = 57.0  # just under the crown cap edge: no bare scalp between crown and lock root
        if lk["role"] == "bang":
            lk["root"]["elev"] = 58.0
            lk["layer"] = 0.002 if (i % 2) else 0.0
    # hanging locks alternate inner/outer shells in azimuth ring order (index order broke alternation at S/K seams)
    ring = sorted((lk for lk in bp["locks"] if lk["role"] in ("side", "back", "face_frame")),
                  key=lambda lk: lk["root"]["az"] % 360)
    for i, lk in enumerate(ring):
        lk["shell"] = "outer" if i % 2 else "inner"
        lk["layer"] = 0.010 if i % 2 else 0.0  # outer shell sits ~ half the neighbour's mid thickness further out
    for j, az in enumerate((-70, 70, -110, 110, -145, 145, 180)):
        bp["locks"].append({"id": f"T0{j + 1}", "role": "top", "root": {"elev": 63, "az": az},
                            "tip": {"elev": 36, "az": az * 1.02 if abs(az) < 170 else az}, "hang_to_y": None,
                            "length": 0.065, "width": [0.050, 0.058, 0.012], "thickness": [0.005, 0.006, 0.002],
                            "clear": 0.0015, "bend": 0.003, "layer": 0.0})
    tops = sorted((lk for lk in bp["locks"] if lk["role"] == "top"), key=lambda lk: lk["root"]["az"] % 360)
    for i, lk in enumerate(tops):  # top cover tiles alternate too (35 deg spacing < tile width)
        lk["shell"] = "outer" if i % 2 else "inner"
        lk["layer"] = 0.003 if i % 2 else 0.0
    for lk in bp["locks"]:
        lk.setdefault("shell", "inner" if lk["role"] == "top" else ("outer" if lk.get("layer", 0) > 0 else "inner"))
        layer_toggle[lk["id"]] = lk["layer"]
    ax = bp["head"]["semi_axes_xyz"]
    for lk in bp["locks"]:
        lk["registry"] = registry(ax, lk)
    bp["targets"] = {
        "length": {"tolerance": 0.006}, "width_root": {"tolerance": 0.004}, "width_mid": {"tolerance": 0.004},
        "thickness_root": {"tolerance": 0.003}, "thickness_mid": {"tolerance": 0.003}, "taper_085": {"tolerance": 0.12},
        "kappa_50": {"tolerance_rel": 0.30, "tolerance_abs": 2.0},
        "min_head_clearance": {"value": 0.0015, "tolerance": 0.0014},
        "max_penetration_depth": {"value": 0.0, "tolerance": 0.0010,
                                  "note": "vertex of one lock inside another closed lock deeper than 1 mm = penetration"}}
    bp["layers"] = {"top": "cover under the crown edge (clear 1.5 mm), inner/outer tiles 0 / 3 mm", "hanging": "inner/outer shells alternating in azimuth ring order, 0 / 10 mm",
                    "bang": "alternating 0 / 2 mm", "crown_edge_elev_deg": CROWN_EDGE_ELEV}
    bp["not_inferred"] = "numeric qualification design; registry values computed from the design spine and profiles"
    (HERE / "qual_hair_blueprint_v3.json").write_text(json.dumps(bp, indent=1, ensure_ascii=False) + "\n")
    print(len(bp["locks"]), "locks")


if __name__ == "__main__":
    main()
