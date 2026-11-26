"""LIND-BUILD-01 technical QA (G3 evidence only; never art approval).

Usage: python3 tools/map_blender/lind/buildings/qa_buildings.py --run DIR --out docs/qa/lind/buildings
Reads DIR/build_manifest.json + renders, the pinned HOME contract, and writes tech_qa_report.json/.md.
Every check is PASS / FAIL / WARN / NOT_RUN. Exit code 1 if any FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import kit_config  # noqa: E402  (pure python, no bpy)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    man = json.load(open(os.path.join(a.run, "build_manifest.json"), encoding="utf-8"))
    cfg, info = kit_config.load_config(REPO)
    contract = cfg["contract_raw"]
    checks = []

    def add(scope, name, status, detail):
        checks.append({"scope": scope, "check": name, "status": status, "detail": detail})

    # ---- contract load
    mc = man["contract"]
    ok = (mc.get("status") == "HOME_CONTRACT_V1_APPLIED" and not mc.get("fallback_used")
          and mc.get("home_contract_sha256") == kit_config.HOME_CONTRACT_SHA256_PIN)
    add("global", "CONTRACT_LOAD", "PASS" if ok else "FAIL",
        {"path": mc.get("home_contract_path"), "sha256": mc.get("home_contract_sha256"),
         "pin": kit_config.HOME_CONTRACT_SHA256_PIN, "fallback_used": mc.get("fallback_used")})
    contract_mats = set(contract.get("materials", {}).keys())
    op = contract["openings"]
    sizes = {"door": (op["door_main_ext"]["clear_w"], op["door_main_ext"]["clear_h"]),
             "door2": (op["door_secondary"]["clear_w"], op["door_secondary"]["clear_h"]),
             "W1": (op["window_W1_ground"]["clear_w"], op["window_W1_ground"]["clear_h"]),
             "W2": (op["window_W2_gable_loft"]["clear_w"], op["window_W2_gable_loft"]["clear_h"]),
             "W3": (op["window_W3_small"]["clear_w"], op["window_W3_small"]["clear_h"])}
    pr = contract["roof"]["pitch_deg"]
    budget = contract["lod_budgets_tris"]
    ids = contract["naming"]["bldg_ids"]
    id_patterns = [re.escape(v).replace("<nn>", r"\d\d") for v in ids.values()]
    for e in man["entries"]:
        sc = f'{e["building"]}/{e["state"]}'
        bid = e["bldg_id"]
        m = e["mesh"]
        lim = budget["LOD0_master_house_shell"] if e["building"] == "inn" else budget["dwelling_LOD0_shell_for_BUILD"]
        add(sc, "tris_budget_LOD0", "PASS" if m["tris"] <= lim else "FAIL", {"tris": m["tris"], "limit": lim})
        add(sc, "uv_map_named_UVMap", "PASS" if not m["meshes_without_UVMap"] else "FAIL", m["meshes_without_UVMap"])
        add(sc, "wall_shell_manifold", "PASS" if m["walls_nonmanifold_edges"] == 0 else "FAIL",
            {"nonmanifold_edges": m["walls_nonmanifold_edges"]})
        add(sc, "material_count<=contract", "PASS" if m["material_count"] <= contract["max_unique_materials_per_building"]
            else "FAIL", {"count": m["material_count"], "limit": contract["max_unique_materials_per_building"]})
        extra = sorted(set(m["materials"]) - contract_mats)
        add(sc, "material_ids_in_contract", "PASS" if not extra else "FAIL",
            {"not_in_contract": extra, "note": "requested as HOME v2 additions (HOME_CONTRACT_ALIGNMENT.md)" if extra else ""})
        add(sc, "pbr_textures_loaded", "PASS" if not e["textures"]["missing"] else "FAIL",
            {"loaded": sorted(set(e["textures"]["loaded"])), "missing": e["textures"]["missing"]})
        p = e["dims"]["pitch_deg"]
        add(sc, "roof_pitch_in_contract_range", "PASS" if pr[0] <= p <= pr[1] else "FAIL",
            {"pitch": p, "range": pr[:2], "contract_default": pr[2], "note": "44 deg documented BUILD choice"})
        # openings
        bad, nonc, spacing = [], [], []
        for wid, ol in e["layout"].items():
            wl = e["walls"][wid]
            rects = []
            for o in ol:
                if o["kind"] in sizes:
                    if (round(o["w"], 3), round(o["h"], 3)) != tuple(round(x, 3) for x in sizes[o["kind"]]):
                        bad.append({"wall": wid, **o})
                else:
                    nonc.append({"wall": wid, "kind": o["kind"], "w": o["w"], "h": o["h"]})
                u = wl["L"] / 2 + o["uc"] + wl["corner_offset"]
                rects.append((u - o["w"] / 2, u + o["w"] / 2, o["z0"], o["z0"] + o["h"], o["kind"]))
            for r in rects:
                if r[4] == "slit":
                    continue
                dmin = min(r[0], wl["outer_len"] - r[1])
                if dmin < op["min_distance_opening_to_corner"] - 1e-6:
                    spacing.append({"wall": wid, "kind": r[4], "issue": "corner", "dist": round(dmin, 3)})
            for i in range(len(rects)):
                for j in range(i + 1, len(rects)):
                    r1, r2 = rects[i], rects[j]
                    if min(r1[3], r2[3]) - max(r1[2], r2[2]) <= 0:
                        continue
                    gap = max(r2[0] - r1[1], r1[0] - r2[1])
                    if 0 <= gap < op["min_pier_between_openings"] - 1e-6 or gap < 0:
                        spacing.append({"wall": wid, "pair": [r1[4], r2[4]], "issue": "pier", "gap": round(gap, 3)})
        add(sc, "opening_clear_sizes=contract", "PASS" if not bad else "FAIL", bad)
        add(sc, "non_contract_opening_types", "WARN" if nonc else "PASS",
            {"types": nonc, "note": "BUILD-specific (bay/ddoor/slit) requested as contract additions" if nonc else ""})
        add(sc, "opening_pier_and_corner_spacing", "PASS" if not spacing else "FAIL", spacing)
        # slates
        n = e["stats"].get("slates", 0)
        u = e.get("slate_unique_dims", 0)
        add(sc, "slate_individual_variation", "PASS" if n > 0 and u / max(n, 1) >= 0.95 else "FAIL",
            {"slates": n, "unique_w_l_t_mm": u, "ratio": round(u / max(n, 1), 4),
             "note": "stopped family H-A had 672 identical slates"})
        # anchors
        rx_id = "^(" + "|".join(id_patterns) + ")$"
        id_ok = re.match(rx_id, bid) is not None
        add(sc, "bldg_id_in_contract", "PASS" if id_ok else "FAIL",
            {"bldg_id": bid, "contract_ids": list(ids.values())})
        names = e["anchors"]
        door_ok = (f"ANC_{bid}_DOOR_MAIN_EXT" in names and f"ANC_{bid}_DOOR_MAIN_INT" in names)
        rx = re.compile(rf"^ANC_{bid}_(DOOR_[A-Z0-9]+_(EXT|INT)|SPAWN_[A-Z0-9]+|SAVE_[A-Z0-9]+|EVENT_[A-Z0-9]+)$")
        badn = [x for x in names if not rx.match(x)]
        ao = e["anchor_offsets"]
        off_ok = abs(ao["ext_from_facade_m"] - 0.6) < 1e-3 and abs(ao["int_from_inner_face_m"] - 0.6) < 1e-3 \
            and abs(ao["ext_z"]) < 1e-3 and abs(ao["int_z"] - ao["ffl"]) < 1e-3
        add(sc, "anchor_naming_and_offsets", "PASS" if door_ok and not badn and off_ok else "FAIL",
            {"names": names, "bad_names": badn, "offsets": ao})
        # render
        if e.get("render_png"):
            pth = os.path.join(a.run, e["render_png"])
            try:
                from PIL import Image
                im = Image.open(pth)
                al = im.getchannel("A")
                w, h = im.size
                cov = sum(1 for v in al.resize((w // 4, h // 4)).getdata() if v > 8) / ((w // 4) * (h // 4))
                border = max(max(al.crop((0, 0, w, 2)).getdata()), max(al.crop((0, h - 2, w, h)).getdata()),
                             max(al.crop((0, 0, 2, h)).getdata()), max(al.crop((w - 2, 0, w, h)).getdata()))
                st = "PASS" if (sha(pth) == e["render_sha256"] and max(w, h) <= 1280 and 0.05 < cov < 0.95) else "FAIL"
                add(sc, "render_png_integrity", st, {"sha_match": sha(pth) == e["render_sha256"], "size": [w, h],
                                                     "alpha_coverage": round(cov, 3), "border_alpha_max": border,
                                                     "note": "shadow-catcher alpha may touch border"})
            except Exception as ex:  # pragma: no cover
                add(sc, "render_png_integrity", "FAIL", str(ex))
        else:
            add(sc, "render_png_integrity", "NOT_RUN", "no render in this run")
    summary = {s: sum(1 for c in checks if c["status"] == s) for s in ("PASS", "FAIL", "WARN", "NOT_RUN")}
    rep = {"task_id": "LIND-BUILD-01", "gate": "G3_TECHNICAL_ONLY (not G2 art)", "blender": man.get("blender"),
           "run_dir": os.path.relpath(a.run, REPO) if a.run.startswith(REPO) else a.run, "summary": summary,
           "contract_load_evidence": {k: v for k, v in info.items() if k != "build_extra"},
           "checks": checks}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "tech_qa_report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "contract_load_evidence.json"), "w", encoding="utf-8") as fh:
        json.dump(rep["contract_load_evidence"], fh, indent=1)
    lines = ["# LIND-BUILD-01 technical QA (G3 evidence only)", "",
             f"Run: `{rep['run_dir']}` — Blender {rep['blender']} — summary {summary}", "",
             "| scope | check | status | detail |", "|---|---|---|---|"]
    for c in checks:
        d = json.dumps(c["detail"], ensure_ascii=False)
        lines.append(f"| {c['scope']} | {c['check']} | {c['status']} | {d[:220]} |")
    open(os.path.join(a.out, "tech_qa_report.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(json.dumps(summary))
    return 1 if summary["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
