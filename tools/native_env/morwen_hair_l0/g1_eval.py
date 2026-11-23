#!/usr/bin/env python3
"""Executable G1 (design conformance) check for a Morwen hair candidate against morwen_hair_l0_blueprint_v1.json.

usage: g1_eval.py CANDIDATE.json [--render-dir DIR]
CANDIDATE.json: {"views": {"front": {"render": "front.png" (registered 384x1024, same camera/registration as the
source), "locks": {"BG_C": [[x,y],...root->tip]}, "points": {"parting_point_front": [x,y]}}}, ...}
Renders are segmented with the same hair mask as the blueprint. Reports PASS/FAIL/NOT_RUN per criterion; never
asserts PASS for a criterion whose input is missing."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_l0_hair_blueprint as B  # noqa: E402


def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))


def mask_from_rows(rows, shape=(1024, 384)):
    m = np.zeros(shape, bool)
    for y, x0, x1 in rows:
        m[y:y + 5, x0:x1 + 1] = True
    return m


def evaluate(bp, cand, base):
    res = {"criteria": {}, "status": None}
    C = res["criteria"]
    for v, sil in bp["silhouettes"].items():
        cv = cand.get("views", {}).get(v, {})
        if "render" not in cv:
            C[f"silhouette_iou_{v}"] = {"status": "NOT_RUN", "reason": "no render"}
            continue
        m = B.hair_mask(base / cv["render"])
        ref = mask_from_rows(sil["rows_y_xmin_xmax"])
        got = mask_from_rows(B.silhouette_rows(m))  # compare at the same 5 px row sampling
        val = iou(ref, got)
        C[f"silhouette_iou_{v}"] = {"value": round(val, 4), "limit": ">= 0.92", "status": "PASS" if val >= 0.92 else "FAIL"}
    for pid, p in bp["points"].items():
        cp = cand.get("views", {}).get(p["view"], {}).get("points", {}).get(pid)
        if cp is None:
            C[f"point_{pid}"] = {"status": "NOT_RUN"}
            continue
        lim = 3 if pid in ("parting_point_front", "whorl_back", "nape_notch_back", "crown_notch_front") else 4
        e = float(np.hypot(cp[0] - p["xy_px"][0], cp[1] - p["xy_px"][1]))
        C[f"point_{pid}"] = {"error_px": round(e, 2), "limit_px": lim, "status": "PASS" if e <= lim else "FAIL"}
    for lid, L in bp["locks"].items():
        for v, e in L["views"].items():
            cl = cand.get("views", {}).get(v, {}).get("locks", {}).get(lid)
            key = f"lock_{lid}_{v}"
            if cl is None:
                C[key] = {"status": "NOT_RUN"}
                continue
            u = e["unc_px"]
            tip = float(np.hypot(*(np.array(cl[-1]) - e["points_px"][-1])))
            root = float(np.hypot(*(np.array(cl[0]) - e["points_px"][0])))
            r = {"tip_error_px": round(tip, 2), "tip_limit_px": max(4, 1.5 * u),
                 "root_error_px": round(root, 2), "root_limit_px": max(5, 2 * u)}
            ok = tip <= r["tip_limit_px"] and root <= r["root_limit_px"]
            m = B.metrics([tuple(p) for p in cl]) if len(cl) >= 3 else None
            if m and "metrics" in e:
                k0, sd = e["metrics"]["kappa_50"], e["metrics_sd"]["kappa_50"]
                lim = 2 * sd + 0.5
                r.update({"kappa_50": round(m["kappa_50"], 4), "kappa_50_target": k0, "kappa_50_limit": round(lim, 4)})
                same_sign = (m["kappa_50"] * k0 >= 0) or abs(k0) <= lim  # sign only enforced where it is resolved
                ok &= abs(m["kappa_50"] - k0) <= lim and same_sign
            r["status"] = "PASS" if ok else "FAIL"
            C[key] = r
    st = [c["status"] for c in C.values()]
    res["counts"] = {s: st.count(s) for s in ("PASS", "FAIL", "NOT_RUN")}
    res["status"] = "FAIL" if "FAIL" in st else ("NOT_RUN" if "NOT_RUN" in st else "PASS")
    return res


if __name__ == "__main__":
    bp = json.loads((HERE / "morwen_hair_l0_blueprint_v1.json").read_text())
    cp = Path(sys.argv[1])
    base = Path(sys.argv[sys.argv.index("--render-dir") + 1]) if "--render-dir" in sys.argv else cp.parent
    out = evaluate(bp, json.loads(cp.read_text()), base)
    print(json.dumps({"status": out["status"], "counts": out["counts"]}))
    (cp.parent / (cp.stem + "_g1.json")).write_text(json.dumps(out, indent=1))
