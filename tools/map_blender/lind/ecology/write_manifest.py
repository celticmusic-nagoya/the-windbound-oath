"""Write docs/production/lind/ecology/eco-asset-manifest.v1.json from the static budget table
plus the latest build record (/tmp/lind_eco/eco_kit_build.json) and renders.json.
Pure python (no bpy): python3 tools/map_blender/lind/ecology/write_manifest.py"""
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
PKG = REPO / "assets" / "candidates" / "LIND-ECO-01" / "eco_kit_v1"
OUT = REPO / "docs" / "production" / "lind" / "ecology" / "eco-asset-manifest.v1.json"

# id: (LOD0 tri budget, instance budget per 50x50 m world tile, provisional zone(s), LOD1 plan)
BUDGET = {
    "eco_tree_deciduous_a": (25000, 40, ["village", "N_farmland_edge", "E_riverbank"], "impostor billboard"),
    "eco_tree_apple_a": (20000, 30, ["orchard"], "impostor billboard"),
    "eco_tree_forest_tall_a": (25000, 60, ["SE_moss_forest_edge"], "impostor billboard"),
    "eco_tree_conifer_a": (25000, 60, ["SE_forest", "N_hills"], "impostor billboard"),
    "eco_grass_tuft_short": (6000, 600, ["village", "paths"], "eco_grass_card_lod1"),
    "eco_grass_meadow": (6000, 500, ["meadow", "field_margin"], "eco_grass_card_lod1"),
    "eco_grass_tall_lax": (7000, 300, ["field_margin", "orchard_floor"], "eco_grass_card_lod1"),
    "eco_grass_coastal_dune": (6000, 400, ["SW_coast"], "card (todo)"),
    "eco_reed_riverside": (4000, 200, ["E_riverbank"], "card (todo)"),
    "eco_sedge_bank": (5000, 300, ["E_riverbank", "ditches"], "eco_grass_card_lod1"),
    "eco_rocks_river": (12000, 60, ["E_river_bed"], "decimate 25%"),
    "eco_rocks_coastal": (24000, 30, ["SW_coast", "W_cliffs_foot"], "decimate 25%"),
    "eco_river_water": (6000, 8, ["E_river"], "same mesh, lower nv"),
    "eco_river_bank": (6000, 8, ["E_river"], "replaced by WORLD terrain"),
    "eco_wheat_patch": (80000, 40, ["N_farmland"], "wheat card strip (todo)"),
    "eco_vegetable_rows": (22000, 20, ["N_farmland", "village_gardens"], "decimate"),
    "eco_flower_patch": (50000, 20, ["N_farmland", "village"], "card (todo)"),
    "eco_hedgerow": (40000, 40, ["field_boundaries"], "card shell (todo)"),
    "eco_fence_post_rail": (2000, 80, ["field_boundaries", "pens"], "same"),
    "eco_haystack": (10000, 10, ["N_farmland", "barns"], "same"),
    "eco_chicken_hen_blockout": (8000, 0, ["coops (blockout only, do not place)"], "n/a"),
    "eco_cow_blockout": (10000, 0, ["pasture (blockout only, do not place)"], "n/a"),
    "eco_grass_card_lod1": (12, 4000, ["far meadow"], "n/a"),
}


def main():
    build = json.loads(pathlib.Path("/tmp/lind_eco/eco_kit_build.json").read_text())
    reg_p = PKG / "renders" / "renders.json"
    reg = json.loads(reg_p.read_text()) if reg_p.exists() else {"files": {}}
    assets = []
    for a in build["assets"]:
        b = BUDGET[a["id"]]
        assets.append({
            "id": a["id"], "category": a["category"], "status": a["status"],
            "generator": a["generator"], "params": a.get("params", {}), "seed": a["seed"],
            "triangles_lod0": a["triangles"], "budget_tris_lod0": b[0], "within_budget": a["triangles"] <= b[0],
            "instance_budget_per_50m_tile": b[1], "zones_provisional": b[2], "lod1_plan": b[3],
            "materials": a["materials"], "wind": a.get("wind"), "water": a.get("water"),
            "dimensions_m": a.get("dimensions_m"), "geometry_sha256": a["geometry_sha256"],
            "info": a.get("info"),
        })
    blend = build.get("blend", {})
    man = {
        "schema": "lind-eco-asset-manifest-v1", "task_id": "LIND-ECO-01", "candidate_id": "eco_kit_v1",
        "branch": "feature/lind-ecology-01", "status": "CANDIDATE_NOT_ADOPTED",
        "gates": {"G1": "BLOCKED", "G2": "NOT_RUN (independent review pending)", "G3": "see docs/qa/lind/ecology/eco_tech_qa.json", "G4": "NOT_RUN"},
        "blender_version": build["blender_version"], "seed": build["seed"],
        "combined_geometry_sha256": build["combined_geometry_sha256"],
        "script_sha256": build["script_sha256"], "textures_sha256": build.get("textures_sha256"),
        "channels": build["channels"],
        "placement": "PROVISIONAL_NOT_LOCKED (WORLD lane stopped; zones are canon-text directions only)",
        "visual_reference": {"path": "assets/sources/lind-world-20261116/original.png",
                             "sha256": "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620",
                             "use": "vegetation character only, not to scale"},
        "blend": {"path": "assets/candidates/LIND-ECO-01/eco_kit_v1/eco_kit_v1.blend",
                  "sha256": blend.get("sha256"), "bytes": blend.get("bytes")},
        "renders": reg.get("files", {}),
        "assets": assets,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print("wrote", OUT, "assets", len(assets), "over_budget", [a["id"] for a in assets if not a["within_budget"]])


if __name__ == "__main__":
    main()
