"""LIND-ECO-01 technical QA (G3 evidence only; does NOT judge art quality / G2).

  flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/ecology/qa_eco.py
Writes docs/qa/lind/ecology/eco_tech_qa.json and prints a summary. Exit 1 on any FAIL.

Checks
  determinism   : two fresh in-process builds -> identical per-asset geometry hashes (+ vs build record)
  budgets       : triangles per asset vs ECO budget table (eco-asset-manifest.v1.json)
  wind channel  : scene props, controller drivers, LIND_Wind on every wind asset, wind_weight attr in [0,1];
                  evaluated displacement f12 vs f30: wind=1 > threshold, wind=0 == 0 exactly; water moves
                  at wind=0 (independent channel); water unaffected by wind value
  alpha         : card textures are true RGBA, binary-ish alpha, transparent texels not white (bleed),
                  icon renders have transparent corners / opaque subject
  render files  : every file in renders.json exists and SHA-256 matches; max dimension <= 1280
  geometry      : no NaN, no zero-area face ratio > 1%, materials assigned, UV present on card meshes
"""
import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import build_eco_assets as B  # noqa: E402
import eco_lib as L  # noqa: E402

REPO = HERE.parents[3]
PKG = B.PKG
QA_DIR = REPO / "docs" / "qa" / "lind" / "ecology"
MANIFEST = REPO / "docs" / "production" / "lind" / "ecology" / "eco-asset-manifest.v1.json"

results = []


def check(name, ok, detail):
    results.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})


def evaluated_co(ob, sc, frame):
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def main():
    out = pathlib.Path("/tmp/lind_eco_qa")
    r1 = B.build(out, save=False)
    r2 = B.build(out, save=True)  # second fresh build (reset_scene inside); keep scene for checks
    h1 = {a["id"]: a["geometry_sha256"] for a in r1["assets"]}
    h2 = {a["id"]: a["geometry_sha256"] for a in r2["assets"]}
    check("determinism_two_builds", h1 == h2,
          {"combined_1": r1["combined_geometry_sha256"], "combined_2": r2["combined_geometry_sha256"],
           "mismatch": [k for k in h1 if h1[k] != h2.get(k)]})
    rec_path = pathlib.Path("/tmp/lind_eco/eco_kit_build.json")
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        check("determinism_vs_render_build", rec["combined_geometry_sha256"] == r2["combined_geometry_sha256"],
              {"render_build": rec["combined_geometry_sha256"], "qa_build": r2["combined_geometry_sha256"]})
    else:
        check("determinism_vs_render_build", False, "missing /tmp/lind_eco/eco_kit_build.json")

    # budgets
    man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"assets": []}
    budget = {a["id"]: a.get("budget_tris_lod0") for a in man.get("assets", [])}
    over, missing = [], []
    for a in r2["assets"]:
        b = budget.get(a["id"])
        if b is None:
            missing.append(a["id"])
        elif a["triangles"] > b:
            over.append((a["id"], a["triangles"], b))
    check("tri_budget_lod0", not over and not missing, {"over": over, "missing_budget": missing,
                                                        "tris": {a["id"]: a["triangles"] for a in r2["assets"]}})

    sc = bpy.context.scene
    # channel plumbing
    ok = (L.WIND_PROP in sc and L.WATER_PROP in sc and bpy.data.objects.get(L.WIND_CTRL)
          and bpy.data.objects.get(L.WATER_CTRL) and bpy.data.node_groups.get(L.WIND_GROUP)
          and bpy.data.node_groups.get(L.WATER_GROUP))
    drv = {}
    for nm in (L.WIND_CTRL, L.WATER_CTRL):
        ob = bpy.data.objects.get(nm)
        ad = ob.animation_data if ob else None
        drv[nm] = [d.driver.variables[0].targets[0].data_path for d in ad.drivers] if ad else []
    ok = ok and drv[L.WIND_CTRL] == ['["%s"]' % L.WIND_PROP] and drv[L.WATER_CTRL] == ['["%s"]' % L.WATER_PROP]
    check("channel_plumbing", bool(ok), {"drivers": drv, "wind_world_space": bool(bpy.data.node_groups[L.WIND_GROUP].get("lind_world_space_wind", False))})

    wind_assets = [a for a in r2["assets"] if a.get("wind")]
    water_assets = [a for a in r2["assets"] if a.get("water")]
    bad_mod, bad_attr = [], []
    for a in wind_assets:
        ob = bpy.data.objects[a["id"]]
        if not any(m.type == "NODES" and m.node_group and m.node_group.name == L.WIND_GROUP for m in ob.modifiers):
            bad_mod.append(a["id"])
        at = ob.data.attributes.get("wind_weight")
        if at is None:
            bad_attr.append(a["id"])
        else:
            v = np.empty(len(at.data))
            at.data.foreach_get("value", v)
            if v.min() < 0 or v.max() > 1 or v.max() <= 0:
                bad_attr.append((a["id"], float(v.min()), float(v.max())))
    check("wind_modifier_and_weights", not bad_mod and not bad_attr,
          {"wind_assets": len(wind_assets), "missing_modifier": bad_mod, "bad_wind_weight": bad_attr})

    # motion: wind on vs wind-stop, water independent
    motion = {}
    halt_ok, move_ok = True, True
    for a in wind_assets:
        ob = bpy.data.objects[a["id"]]
        L.set_channel(sc, wind=1.0, water=1.0)
        d1 = float(np.abs(evaluated_co(ob, sc, 12) - evaluated_co(ob, sc, 30)).max())
        L.set_channel(sc, wind=0.0, water=1.0)
        c12 = evaluated_co(ob, sc, 12)
        d0 = float(np.abs(c12 - evaluated_co(ob, sc, 30)).max())
        rest = np.array([v.co[:] for v in ob.data.vertices])
        dr = float(np.abs(c12 - rest).max())
        motion[a["id"]] = {"wind1_f12_vs_f30_max_m": round(d1, 5), "wind0_f12_vs_f30_max_m": d0, "wind0_vs_rest_max_m": dr}
        halt_ok &= (d0 == 0.0 and dr == 0.0)
        move_ok &= d1 > 0.002
    check("wind1_moves", move_ok, {k: v["wind1_f12_vs_f30_max_m"] for k, v in motion.items()})
    check("wind0_halts_exactly", halt_ok, {k: [v["wind0_f12_vs_f30_max_m"], v["wind0_vs_rest_max_m"]] for k, v in motion.items()})
    wat = {}
    wat_ok = bool(water_assets)
    for a in water_assets:
        ob = bpy.data.objects[a["id"]]
        L.set_channel(sc, wind=0.0, water=1.0)
        w0 = evaluated_co(ob, sc, 12)
        dw0 = float(np.abs(w0 - evaluated_co(ob, sc, 30)).max())
        L.set_channel(sc, wind=1.0, water=1.0)
        w1 = evaluated_co(ob, sc, 12)
        indep = float(np.abs(w0 - w1).max())
        L.set_channel(sc, wind=0.0, water=0.0)
        dstop = float(np.abs(evaluated_co(ob, sc, 12) - evaluated_co(ob, sc, 30)).max())
        wat[a["id"]] = {"wind0_water1_f12_vs_f30_max_m": round(dw0, 5), "wind_change_effect_m": indep,
                        "water0_f12_vs_f30_max_m": dstop}
        wat_ok &= dw0 > 0.002 and indep == 0.0 and dstop == 0.0
    check("water_flows_during_wind_stop_and_is_independent", wat_ok, wat)
    L.set_channel(sc, wind=1.0, water=1.0)

    # geometry sanity
    geo = {}
    geo_ok = True
    for a in r2["assets"]:
        ob = bpy.data.objects[a["id"]]
        me = ob.data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        areas = np.empty(len(me.polygons))
        me.polygons.foreach_get("area", areas)
        zero = float((areas < 1e-9).mean()) if len(areas) else 0.0
        nan = bool(np.isnan(co).any())
        nomat = len(me.materials) == 0 or any(m is None for m in me.materials)
        uv_needed = any(m and m.name.startswith(("M_eco_leafcard", "M_eco_grass_card")) for m in me.materials)
        uv_ok = (not uv_needed) or len(me.uv_layers) > 0
        geo[a["id"]] = {"zero_area_ratio": round(zero, 5), "nan": nan, "materials_ok": not nomat, "uv_ok": uv_ok}
        geo_ok &= (zero <= 0.01 and not nan and not nomat and uv_ok)
    check("geometry_sanity", geo_ok, geo)

    # alpha on card textures
    from PIL import Image
    alpha = {}
    a_ok = True
    for tex in sorted((PKG / "textures").glob("*.png")):
        im = Image.open(tex)
        arr = np.asarray(im.convert("RGBA")).astype(np.float32) / 255.0
        al = arr[..., 3]
        frac_t = float((al == 0).mean())
        frac_o = float((al == 1).mean())
        mid = float(((al > 0) & (al < 1)).mean())
        trgb = arr[al == 0][:, :3]
        white = float((trgb.mean(axis=1) > 0.6).mean()) if len(trgb) else 0.0
        alpha[tex.name] = {"mode": im.mode, "size": im.size, "transparent": round(frac_t, 3), "opaque": round(frac_o, 3),
                           "partial": round(mid, 4), "white_fringe_texels": white,
                           "sha256": hashlib.sha256(tex.read_bytes()).hexdigest()}
        a_ok &= im.mode == "RGBA" and frac_t > 0.2 and frac_o > 0.05 and white == 0.0
    icons = sorted((PKG / "renders").glob("icon256_*.png"))
    for ic in icons:
        arr = np.asarray(Image.open(ic).convert("RGBA")).astype(np.float32) / 255.0
        corners = [arr[0, 0, 3], arr[0, -1, 3], arr[-1, 0, 3], arr[-1, -1, 3]]
        subj = float((arr[..., 3] > 0.5).mean())
        alpha[ic.name] = {"mode": Image.open(ic).mode, "corner_alpha_max": float(max(corners)), "subject_coverage": round(subj, 3)}
        a_ok &= Image.open(ic).mode == "RGBA" and max(corners) == 0.0 and subj > 0.01
    check("alpha", a_ok and bool(icons), {"textures_and_icons": alpha, "icons_found": len(icons)})

    # render registry
    reg_p = PKG / "renders" / "renders.json"
    rr = {}
    r_ok = reg_p.exists()
    if r_ok:
        reg = json.loads(reg_p.read_text())
        for nm, info in reg["files"].items():
            f = PKG / "renders" / nm
            if not f.exists():
                rr[nm] = "MISSING"
                r_ok = False
                continue
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            w, h = Image.open(f).size
            rr[nm] = {"sha_match": sha == info["sha256"], "size": [w, h]}
            r_ok &= sha == info["sha256"] and max(w, h) <= 1280
    check("render_registry", r_ok, rr)

    summary = {"task_id": "LIND-ECO-01", "scope": "G3 technical only; G2 art NOT judged here",
               "blender_version": bpy.app.version_string, "seed": B.MASTER_SEED,
               "combined_geometry_sha256": r2["combined_geometry_sha256"],
               "script_sha256": r2["script_sha256"],
               "motion": motion, "water": wat,
               "overall": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
               "checks": results}
    QA_DIR.mkdir(parents=True, exist_ok=True)
    (QA_DIR / "eco_tech_qa.json").write_text(json.dumps(summary, indent=1, default=str))
    for r in results:
        print("%-52s %s" % (r["check"], r["status"]))
    print("OVERALL", summary["overall"])
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
