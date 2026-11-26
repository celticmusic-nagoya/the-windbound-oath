"""LIND-ECO-01 integration v2 — technical QA, CG colour comparison, placement rules, manifest and SHA256SUMS.

  python3 tools/map_blender/lind/ecology/package_integration_v2.py --pkg /tmp/lind_eco_v2 [--copy-to assets/candidates/LIND-ECO-01/integration_v2]

Pure Python (numpy + Pillow). Self/technical QA only: this never records G2 PASS (independent reviewer only) or G4.
"""
import argparse
import colorsys
import hashlib
import json
import pathlib
import shutil

import numpy as np
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parents[4]
CG_CLIFF = REPO / "assets/approved/game/cliff/sunset_background.png"
CG_RILDE = REPO / "assets/approved/world/rilde_village.png"
CG_SHA = {"sunset_background.png": "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07",
          "rilde_village.png": "c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def green_stats(img, box):
    """HSV of vegetation-green pixels (hue 60-150 deg, sat > 0.18, val > 0.04) inside box (fractions)."""
    im = Image.open(img).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = (int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H))
    a = np.asarray(im.crop((x0, y0, x1, y1))).reshape(-1, 3) / 255.0
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in a[:: max(1, len(a) // 40000)]])
    h, s, v = hsv[:, 0] * 360, hsv[:, 1], hsv[:, 2]
    m = (h > 55) & (h < 150) & (s > 0.18) & (v > 0.04)
    if m.sum() < 50:
        return {"green_fraction": float(m.mean()), "n": int(m.sum())}
    return {"green_fraction": round(float(m.mean()), 3), "hue_med": round(float(np.median(h[m])), 1),
            "sat_med": round(float(np.median(s[m])), 3), "val_p5": round(float(np.percentile(v[m], 5)), 3),
            "val_p50": round(float(np.percentile(v[m], 50)), 3), "val_p95": round(float(np.percentile(v[m], 95)), 3),
            "n": int(m.sum())}


PLACEMENT_RULES = {
    "_contract": {
        "units": "metres; provisional asset-local coordinates (director-approved 2026-11-18); NOT a WORLD placement",
        "axes": "glTF Y-up (exported from Blender Z-up); pivot = root at ground contact (y=0); +X east in asset space",
        "wind": "per-vertex _WIND_WEIGHT (0 root .. 1 tip) x node extras eco_wind {amplitude_m, frequency_hz, flutter}; "
                "global input = scene wind channel lind_wind_strength 0..1 (0 = wind-stop event: all sway must reach 0)",
        "prevailing_wind_xy": [0.959, -0.282],
        "colour": "baseColor = baseColorTexture x COLOR_0 (glTF spec); vertex-colour-only meshes have no baseColorTexture",
        "alpha": "leaf/needle cards + impostors: alphaMode MASK cutoff 0.5, doubleSided",
        "game_camera": "fixed 28 deg quarter-view orthographic, 1.75 m figure ~45-48 px on 720 p",
        "lod_policy_game_camera": "the game camera is fixed-distance orthographic, so LOD is chosen per role, not by distance: "
                                  "LOD1 = in-game default; LOD0 = cutscene/close camera only; LOD2 = background rows, "
                                  "distant hills, or Android low tier",
        "density_unit": "instances per 100 m2 of eligible surface, LOD1",
        "exclusions_all": ["building footprints + 0.5 m", "route/path surfaces (Codex ROUTE owner)", "water",
                           "slope > rule.max_slope_deg", "cliff faces (PR #421 rock owner)"],
    },
    "turf_carpet": {"assets": ["eco_turf_meadow_a"], "zones": ["cliff_top_meadow", "village_green", "meadow"],
                    "max_slope_deg": 32, "density": 59, "spacing_m": 1.3, "position_jitter_m": 0.35,
                    "yaw": "random", "scale": [0.95, 1.15], "align_to_normal": 0.85, "sink_m": 0.01,
                    "notes": "tile centres on a 1.3 m jittered grid (~30 % overlap) so feathered edges interleave; "
                             "leave worn bands bare along routes. LOD2 flat decal is a self-FAIL (see QA) — do not use "
                             "as the in-game carpet."},
    "grass_accent": {"assets": ["eco_grass_meadow", "eco_grass_tuft_short"], "zones": ["cliff_top_meadow", "village_verge", "meadow"],
                     "max_slope_deg": 35, "density": 9, "min_spacing_m": 0.8, "yaw": "random", "scale": [0.9, 1.2],
                     "align_to_normal": 0.3, "notes": "on top of turf, clustered near rocks/fences/building feet"},
    "grass_margin": {"assets": ["eco_grass_tall_lax"], "zones": ["field_margin", "fence_foot", "wall_foot"],
                     "max_slope_deg": 30, "density": 12, "min_spacing_m": 0.6, "yaw": "random", "scale": [0.9, 1.15],
                     "align_to_normal": 0.2},
    "grass_cliff_edge": {"assets": ["eco_grass_coastal_dune"], "zones": ["cliff_lip_band_0_3m"],
                         "max_slope_deg": 45, "density": 18, "min_spacing_m": 0.5,
                         "yaw": "align lean to prevailing_wind_xy +- 15 deg (asset is pre-combed)", "scale": [0.9, 1.25],
                         "align_to_normal": 0.5, "notes": "only within 3 m of the cliff lip; never the carpet"},
    "flower_meadow": {"assets": ["eco_flower_daisy_clump"], "zones": ["cliff_top_meadow", "village_verge"],
                      "max_slope_deg": 30, "density": 6, "min_spacing_m": 1.2, "cluster": "2-4 clumps within 1.5 m",
                      "yaw": "random", "scale": [1.0, 1.4], "align_to_normal": 0.2,
                      "notes": "scale up to 1.4 is allowed: approved CGs exaggerate daisy heads for readability"},
    "flower_cliff_cushion": {"assets": ["eco_flower_violet_cushion"], "zones": ["cliff_top_meadow", "cliff_lip_band_0_3m", "rock_edge"],
                             "max_slope_deg": 45, "density": 5, "min_spacing_m": 1.0, "yaw": "random", "scale": [1.0, 1.4],
                             "align_to_normal": 0.7},
    "flower_village": {"assets": ["eco_flower_spike_clump"], "zones": ["village_garden", "wall_foot", "path_edge"],
                       "max_slope_deg": 20, "density": 3, "min_spacing_m": 1.5, "cluster": "2-5 clumps", "yaw": "random",
                       "scale": [0.9, 1.2], "align_to_normal": 0.0, "notes": "not on the exposed cliff top"},
    "moss_cushion": {"assets": ["eco_moss_cushion_a"], "zones": ["rock_base", "wall_foot", "shaded_ground", "woodland_floor"],
                     "max_slope_deg": 40, "density": 4, "min_spacing_m": 0.6, "yaw": "random", "scale": [0.6, 1.3],
                     "align_to_normal": 1.0, "sink_m": 0.005},
    "moss_mat": {"assets": ["eco_moss_mat_b"], "zones": ["rock_top", "wall_top", "roof_ridge"],
                 "rule": "only where surface normal.y > 0.6 (upward-facing); prefer north/shaded side",
                 "yaw": "random", "scale": [0.6, 1.4], "align_to_normal": 1.0,
                 "shader_alternative": "for rocks owned by PR #421 do NOT add geometry; blend textures/moss_tile_* in the rock "
                                       "shader with mask = smoothstep(0.55, 0.8, normal.y) x cavity, tile 0.5 m"},
    "shrub_low": {"assets": ["eco_shrub_round_a"], "zones": ["village_edge", "rock_lee", "field_corner", "cliff_top_lee"],
                  "max_slope_deg": 30, "density": 0.8, "min_spacing_m": 3.0, "yaw": "random", "scale": [0.75, 1.15],
                  "align_to_normal": 0.0, "notes": "on the cliff top only in the lee of rocks/hollows (wind-exposed lip stays open)"},
    "hedgerow": {"assets": ["eco_hedgerow"], "zones": ["field_boundary"], "placement": "along boundary splines, 4.0 m step, "
                 "yaw = spline tangent, scale [0.9, 1.1]", "max_slope_deg": 25},
    "tree_broadleaf": {"assets": ["eco_tree_deciduous_a"], "zones": ["village", "village_green", "cliff_top_inland_edge"],
                       "max_slope_deg": 20, "density": 0.15, "min_spacing_m": 9.0, "yaw": "random", "scale": [0.85, 1.15],
                       "align_to_normal": 0.0, "notes": "single framing trees; none within 15 m of the cliff lip"},
    "tree_woodland": {"assets": ["eco_tree_forest_tall_a"], "zones": ["woodland_edge", "moss_forest_approach"],
                      "max_slope_deg": 25, "density": 0.6, "min_spacing_m": 5.0, "yaw": "random", "scale": [0.85, 1.2]},
    "tree_orchard": {"assets": ["eco_tree_apple_a"], "zones": ["orchard"], "placement": "rows 5 m apart, 4.5 m in-row, "
                     "jitter 0.4 m", "max_slope_deg": 15, "scale": [0.85, 1.1]},
    "tree_conifer": {"assets": ["eco_tree_conifer_a"], "zones": ["hills_background", "forest"],
                     "max_slope_deg": 35, "density": 0.5, "min_spacing_m": 4.5, "yaw": "random", "scale": [0.8, 1.25],
                     "notes": "background silhouettes: LOD2 preferred"},
    "riverbank": {"assets": ["eco_sedge_bank", "eco_reed_riverside"], "zones": ["river_bank_0_2m"], "max_slope_deg": 40,
                  "density": 14, "min_spacing_m": 0.5, "yaw": "random", "scale": [0.9, 1.2], "align_to_normal": 0.4,
                  "notes": "reeds only on the slow inner bank, never over the water surface"},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--copy-to")
    a = ap.parse_args()
    pkg = pathlib.Path(a.pkg)
    build = json.loads((pkg / "integration_build.json").read_text())
    reg = json.loads((pkg / "renders" / "renders_v2.json").read_text())

    # --- technical checks (self QA)
    checks = []
    def chk(name, ok, detail=""):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})
    chk("reused kit geometry matches kit build hashes",
        all(v["matches_kit_build"] for v in build["selection"].values() if v["verdict"] == "PACKAGE"))
    chk("kit combined geometry hash equals CI-verified 344e3229…",
        build["kit_combined_geometry_sha256"] == "344e32294e0c66f769979c7be1d5f594911646bf51c5fcb393eb83190fa66cba")
    for oid, r in build["packaged"].items():
        for l in r["lods"]:
            g = l["glb"]
            ok = "COLOR_0" in g["attributes"] and "_WIND_WEIGHT" in g["attributes"] and "NORMAL" in g["attributes"]
            cards = [m for m in g["materials"] if m["baseColorTexture"]]
            ok_alpha = all(m["alphaMode"] == "MASK" for m in cards if "moss" not in (m["name"] or ""))
            chk(f"{oid} LOD{l['lod']} glb attributes/alpha", ok and ok_alpha,
                f"{l['tris']} tris, {g['bytes']} B, attrs {g['attributes']}")
        tris = [l["tris"] for l in r["lods"]]
        chk(f"{oid} LOD tris strictly decreasing", all(x > y for x, y in zip(tris, tris[1:])), str(tris))
    for name, rec in reg["files"].items():
        p = pkg / "renders" / name
        chk(f"render {name} sha matches registry", p.exists() and sha(p) == rec["sha256"])
        chk(f"render {name} built from current integration_build.json",
            rec["integration_build_sha256"] == sha(pkg / "integration_build.json"))
    for k, v in CG_SHA.items():
        p = CG_CLIFF if k == "sunset_background.png" else CG_RILDE
        chk(f"approved CG {k} unchanged", sha(p) == v)

    # --- CG colour comparison (measurement, not an art verdict)
    colour = {
        "cg_cliff_meadow_foreground": green_stats(CG_CLIFF, (0.0, 0.70, 0.62, 1.0)),
        "cg_rilde_trees_and_verges": green_stats(CG_RILDE, (0.0, 0.10, 1.0, 1.0)),
        "v2_cliffmeadow_sunset_lod0": green_stats(pkg / "renders" / "v2_cliffmeadow_sunset_lod0.png", (0.0, 0.55, 1.0, 1.0)),
        "v2_gameview_turflod1": green_stats(pkg / "renders" / "v2_gameview_28deg_ortho_fig48px_turflod1.png", (0.0, 0.2, 1.0, 0.75)),
        "v2_gameview_turflod2": green_stats(pkg / "renders" / "v2_gameview_28deg_ortho_fig48px_turflod2.png", (0.0, 0.2, 1.0, 0.75)),
        "v2_lineup_tree_crowns": green_stats(pkg / "renders" / "v2_lineup_lod0_day.png", (0.18, 0.08, 0.42, 0.40)),
        "g2_review_01_tree_crowns_reference": {"hue_med": 97, "sat_med": 0.47, "val_p5": 0.03, "val_p50": 0.18, "val_p95": 0.39,
                                               "note": "copied from G2_REVIEW_01 §4 (eco_kit_v1, Cycles materials)"},
    }

    # comparison sheet: CG cliff | v2 vignette | v2 game view
    sheet = Image.new("RGB", (1920, 380), (24, 24, 24))
    for i, p in enumerate((CG_CLIFF, pkg / "renders" / "v2_cliffmeadow_sunset_lod0.png",
                           pkg / "renders" / "v2_gameview_28deg_ortho_fig48px_turflod1.png")):
        im = Image.open(p).convert("RGB")
        im.thumbnail((640, 360))
        sheet.paste(im, (i * 640, 10))
    sp = pkg / "renders" / "v2_compare_cg_cliff_vs_v2.png"
    sheet.save(sp, optimize=True)

    (pkg / "placement_rules.v2.json").write_text(json.dumps(PLACEMENT_RULES, indent=1, ensure_ascii=False))
    qa = {"schema": "two.lind.eco.integration.v2.tech_qa", "scope": "self / technical QA only",
          "checks": checks, "summary": {"PASS": sum(c["result"] == "PASS" for c in checks),
                                        "FAIL": sum(c["result"] == "FAIL" for c in checks)},
          "colour_vs_approved_cg": colour, "comparison_sheet": sp.name,
          "gates": {"G1": "NOT_RUN (no canonical vegetation spec; CG used as art reference only)",
                    "G2": "NOT_RUN for v2 assets — independent reviewer required",
                    "G3": "PARTIAL: export/attribute/LOD/hash checks below; no in-engine validation",
                    "G4": "NOT_RUN (WebGL/Android owned by Codex runtime integration)"}}
    (pkg / "tech_qa_v2.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False))

    # --- SHA256SUMS over every delivered file
    files = sorted(p for p in pkg.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "manifest.v2.json"))
    manifest = {"schema": "two.lind.eco.integration.v2.manifest", "task_id": "LIND-ECO-01",
                "status": "CANDIDATE_FOR_INTEGRATION_TEST — not adopted, no WORLD placement",
                "editable_source": "eco_integration_v2.blend (+ tools/map_blender/lind/ecology/*.py, deterministic)",
                "files": {p.relative_to(pkg).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in files}}
    (pkg / "manifest.v2.json").write_text(json.dumps(manifest, indent=1))
    files.append(pkg / "manifest.v2.json")
    (pkg / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(pkg).as_posix()}\n" for p in files))
    print("QA", qa["summary"], "files", len(files))
    for k, v in colour.items():
        print(k, v)
    if a.copy_to:
        dst = REPO / a.copy_to
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(pkg, dst)
        print("copied to", dst)


if __name__ == "__main__":
    main()
