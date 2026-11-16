"""LIND-BUILD-01 architecture-kit configuration (single source of every dimension).

Authority: HOME lane `arch-kit-contract.v1.json` (LIND-HOME-01, status
CONTRACT_V1_CANDIDATE_NOT_DIRECTOR_LOCKED). `load_config()` reads it (repo copy if present,
otherwise the HOME worktree path, or $LIND_HOME_ARCH_CONTRACT) and derives the kit values from
its defaults/ranges. If the contract cannot be found, the embedded FALLBACK (identical values,
snapshot of contract v1 read 2026-11-16) is used and the status says so.

BUILD-specific values that the contract does not define are in BUILD_EXTRA and listed in
`docs/production/lind/buildings/HOME_CONTRACT_ALIGNMENT.md` (deviations + open questions).

Units: metres, Z-up, main entrance faces -Y, origin = centre of exterior footprint bbox at grade.
"""
from __future__ import annotations

import copy
import json
import os

# Pinned HOME contract v1 (vendored byte-identical, read-only). Loader accepts a file only if its
# SHA-256 equals the pin; otherwise FALLBACK is used and QA must report CONTRACT_LOAD=FAIL.
HOME_CONTRACT_SHA256_PIN = "a415170dfac2d03a71dc973905f5a0ddf707392f10af1c7a755e3f0f37e3c651"
HOME_CONTRACT_CANDIDATES = [
    os.environ.get("LIND_HOME_ARCH_CONTRACT", ""),
    "docs/production/lind/buildings/vendor/arch-kit-contract.v1.json",
    "docs/production/lind/home/arch-kit-contract.v1.json",
    "/home/claude/wt-home/docs/production/lind/home/arch-kit-contract.v1.json",
]
HOME_CONTRACT_SHA256_SEEN = None  # filled at load time

SEED_BASE = 1311  # PR #309 config; building seed = SEED_BASE + 100 * index

# Snapshot of the HOME contract v1 values used (only the keys BUILD consumes).
FALLBACK_CONTRACT = {
    "schema": "lind.arch-kit-contract.v1",
    "levels": {"finished_floor_above_grade": [0.15, 0.30, 0.25], "storey_floor_to_floor": [2.6, 3.0, 2.75],
               "knee_wall_above_loft_floor": [0.0, 0.6, 0.3], "wall_plate_top_z_one_and_half_storey": 3.3},
    "walls": {"exterior_stone_thickness": [0.45, 0.65, 0.55], "plinth_course_height": [0.28, 0.40],
              "course_height": [0.15, 0.32], "quoin_long": [0.48, 0.62], "quoin_short": [0.28, 0.36]},
    "openings": {"door_main_ext": {"clear_w": 1.00, "clear_h": 2.05, "frame": 0.08},
                 "door_secondary": {"clear_w": 0.90, "clear_h": 2.00, "frame": 0.08},
                 "window_W1_ground": {"clear_w": 0.80, "clear_h": 1.05, "sill_above_ffl": 0.95},
                 "window_W2_gable_loft": {"clear_w": 0.60, "clear_h": 0.75},
                 "window_W3_small": {"clear_w": 0.45, "clear_h": 0.55},
                 "frame_setback_from_exterior_face": 0.14,
                 "lintel": {"height": 0.18, "bearing_each_side": 0.20},
                 "min_pier_between_openings": 0.6, "min_distance_opening_to_corner": 0.7},
    "roof": {"pitch_deg": [38, 48, 42], "eave_overhang": [0.35, 0.45, 0.40], "verge_overhang": [0.25, 0.35, 0.30],
             "rafter": {"w": 0.08, "h": 0.15, "spacing": 0.60}, "bargeboard": {"w": 0.05, "h": 0.22},
             "slate_spec": {"colour_hsv_candidate": {"h_deg": [200, 215], "s": [0.08, 0.15], "v_srgb": [0.32, 0.45]},
                            "exposed_gauge": [0.15, 0.20], "length": [0.34, 0.44], "width": [0.18, 0.32],
                            "thickness": [0.010, 0.020]}},
    "chimney": {"plan": [0.9, 0.75], "above_ridge_min": 0.6, "cap_slab_overhang": 0.06, "pots": [1, 2]},
    "max_unique_materials_per_building": 16,
    "render_standards": {"game_camera": {"type": "ORTHO", "elevation_deg": 27, "azimuth_deg": -45},
                         "preview_max_px": 1280, "game_scale_px": [48, 96]},
}

# BUILD-only values not covered by the contract (documented in HOME_CONTRACT_ALIGNMENT.md)
BUILD_EXTRA = {
    "pitch_deg_build": 44.0,          # inside contract range 38-48; CG reads steep (see programme §2)
    "slate_gauge": 0.18,              # inside 0.15-0.20
    "batten_section": [0.05, 0.03],
    "ridge_piece_len": [0.30, 0.40],
    "wall_texture_tile_m": 3.2,       # DEVIATION: 320 px/m (contract 512 +-25%); 2.0 m tile rendered stones ~0.15 m (brick-like) vs CG ~0.3-0.5 m
    "dressed_texture_tile_m": 1.0,
    "plinth_height": 0.32,            # inside 0.28-0.40
    "quoin_course_h": [0.22, 0.32],   # inside course_height 0.15-0.32
    "quoin_proud": 0.03,
    "eave_wall_inner_knee": 0.30,
    "porch": {"post": 0.16, "eave_z": 2.55, "pitch_deg": 44.0, "depth": 1.45},
    "dormer": {"w": 1.30, "front_h": 1.20, "pitch_deg": 46.0},
    "render": {"engine": "CYCLES", "samples": 48, "denoise": True, "max_px": 1280},
}

BUILDINGS = {
    # w = world X extent, d = world Y extent (front facade on -Y)
    "inn": {"index": 0, "bldg_id": "INN", "w": 12.0, "d": 8.0, "storeys": 2, "front": "eaves",
            "cross_gable": {"w": 4.4, "proj": 1.5}, "chimneys": ["left", "right"],
            "dormers": [-3.7, 3.7], "porch": None, "sign": "weathercock", "size_class": "L",
            "runtime_maps": ["rilde_in_inn_1f", "rilde_in_inn_2f"]},
    "shop": {"index": 1, "bldg_id": "SHOP", "w": 6.6, "d": 8.4, "storeys": 1, "attic": True, "front": "gable",
             "chimneys": ["side_right"], "dormers": [], "porch": None, "awning": True,
             "sign": "pouch_leaf", "size_class": "M", "runtime_maps": ["rilde_in_shop"]},
    "house_a": {"index": 2, "bldg_id": "DWELL01", "w": 7.4, "d": 5.6, "storeys": 1, "attic": True, "front": "eaves",
                "chimneys": ["right"], "dormers": [-1.6], "porch": "pent", "sign": None, "size_class": "S",
                "runtime_maps": ["rilde_in_house_01"]},
    "house_b": {"index": 3, "bldg_id": "DWELL02", "w": 5.8, "d": 7.2, "storeys": 1, "attic": True, "front": "gable",
                "chimneys": ["side_left"], "dormers": [], "porch": "gabled", "sign": None, "size_class": "S",
                "runtime_maps": ["rilde_in_house_02"]},
    "house_c": {"index": 4, "bldg_id": "DWELL03", "w": 7.6, "d": 5.4, "storeys": 1, "attic": True, "front": "eaves",
                "chimneys": ["left"], "dormers": [], "porch": None, "lean_to": {"side": "right", "w": 2.4},
                "sign": None, "size_class": "S", "runtime_maps": ["rilde_in_house_03"]},
    "storage": {"index": 5, "bldg_id": "STORE01", "w": 6.6, "d": 7.6, "storeys": 1, "attic": True, "front": "gable",
                "chimneys": [], "dormers": [], "porch": None, "board_gable": True,
                "hoist": True, "double_door": True, "sign": None, "size_class": "M",
                "runtime_maps": ["rilde_in_storage"]},
}


def _default(v):
    return v[2] if isinstance(v, list) and len(v) == 3 else v


def load_config(repo_root=None):
    global HOME_CONTRACT_SHA256_SEEN
    import hashlib
    contract, src = None, None
    tried = []
    for cand in HOME_CONTRACT_CANDIDATES:
        if not cand:
            continue
        path = cand if (os.path.isabs(cand) or repo_root is None) else os.path.join(repo_root, cand)
        if os.path.isfile(path):
            raw = open(path, "rb").read()
            sha = hashlib.sha256(raw).hexdigest()
            tried.append({"path": path, "sha256": sha, "pin_match": sha == HOME_CONTRACT_SHA256_PIN})
            if sha == HOME_CONTRACT_SHA256_PIN:
                contract = json.loads(raw)
                src = path
                HOME_CONTRACT_SHA256_SEEN = sha
                break
        else:
            tried.append({"path": path, "missing": True})
    status = "HOME_CONTRACT_V1_APPLIED" if contract else "FALLBACK_SNAPSHOT_OF_HOME_CONTRACT_V1"
    c = contract or copy.deepcopy(FALLBACK_CONTRACT)
    if contract is not None:
        info_materials = sorted(contract.get("materials", {}).keys())
    else:
        info_materials = []
    lv, wl, op, rf = c["levels"], c["walls"], c["openings"], c["roof"]
    ss = rf["slate_spec"]
    hsv = ss["colour_hsv_candidate"]
    cfg = {
        "levels": {"ffl": _default(lv["finished_floor_above_grade"]),
                   "storey": _default(lv["storey_floor_to_floor"]),
                   "knee": _default(lv["knee_wall_above_loft_floor"]),
                   "plate_1_5": lv["wall_plate_top_z_one_and_half_storey"]},
        "walls": {"thickness": _default(wl["exterior_stone_thickness"]),
                  "plinth_height": BUILD_EXTRA["plinth_height"],
                  "quoin_long": wl["quoin_long"], "quoin_short": wl["quoin_short"],
                  "quoin_course_h": BUILD_EXTRA["quoin_course_h"], "quoin_proud": BUILD_EXTRA["quoin_proud"],
                  "texture_tile_m": BUILD_EXTRA["wall_texture_tile_m"],
                  "dressed_tile_m": BUILD_EXTRA["dressed_texture_tile_m"]},
        "openings": {"door": op["door_main_ext"], "door2": op["door_secondary"],
                     "W1": op["window_W1_ground"], "W2": op["window_W2_gable_loft"], "W3": op["window_W3_small"],
                     "setback": op["frame_setback_from_exterior_face"], "lintel": op["lintel"],
                     "min_pier": op["min_pier_between_openings"], "min_corner": op["min_distance_opening_to_corner"]},
        "roof": {"pitch_deg": BUILD_EXTRA["pitch_deg_build"],
                 "pitch_range": [rf["pitch_deg"][0], rf["pitch_deg"][1]],
                 "eave_overhang": _default(rf["eave_overhang"]),
                 "verge_overhang": _default(rf["verge_overhang"]),
                 "rafter_spacing": rf["rafter"]["spacing"],
                 "rafter_section": [rf["rafter"]["w"], rf["rafter"]["h"]],
                 "bargeboard": [rf["bargeboard"]["w"], rf["bargeboard"]["h"]],
                 "batten_section": BUILD_EXTRA["batten_section"],
                 "slate_length": ss["length"], "slate_width": ss["width"], "slate_thickness": ss["thickness"],
                 "slate_gauge": BUILD_EXTRA["slate_gauge"],
                 "slate_hsv": hsv, "ridge_piece_len": BUILD_EXTRA["ridge_piece_len"]},
        "chimney": c["chimney"],
        "porch": BUILD_EXTRA["porch"],
        "dormer": BUILD_EXTRA["dormer"],
        "camera": c["render_standards"]["game_camera"],
        "render": BUILD_EXTRA["render"],
        "max_materials": c.get("max_unique_materials_per_building", 16),
    }
    info = {"status": status, "fallback_used": contract is None, "pin_sha256": HOME_CONTRACT_SHA256_PIN,
            "candidates_tried": tried,
            "home_contract_path": src, "home_contract_sha256": HOME_CONTRACT_SHA256_SEEN,
            "home_contract_status": c.get("status"), "build_extra": BUILD_EXTRA,
            "contract_material_ids": info_materials}
    cfg["contract_raw"] = c
    return cfg, info


if __name__ == "__main__":
    cfg, info = load_config()
    print(json.dumps({"info": info, "cfg": cfg}, indent=1))
