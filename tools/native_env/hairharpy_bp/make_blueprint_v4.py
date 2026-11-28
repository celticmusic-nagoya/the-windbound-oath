#!/usr/bin/env python3
"""Generate qual_hair_blueprint_v4.json from v3 (G2 self-findings r5): the 7 flat top tiles become a 12-lock whorl
from near the apex (root elev 76, tip elev 50) that also covers the frontal scalp above the bang roots (elev 58);
bang and hanging mid widths +12 % so neighbouring locks read as one mass. Registry recomputed from the design spine."""
import json
from pathlib import Path

import make_blueprint_v3 as B3

HERE = Path(__file__).resolve().parent
WIDEN = 1.12


def main():
    bp = json.loads((HERE / "qual_hair_blueprint_v3.json").read_text())
    bp["blueprint_id"], bp["schema"] = "QUAL-HH-VOLUME-V4", "two-hair-blueprint/v4"
    bp["locks"] = [lk for lk in bp["locks"] if lk["role"] != "top"]
    for lk in bp["locks"]:
        w = lk["width"]
        lk["width"] = [round(w[0] * WIDEN, 4), round(w[1] * WIDEN, 4), w[2]]
    for j in range(12):
        az = ((30 * j + 180) % 360) - 180
        bp["locks"].append({"id": f"W{j + 1:02d}", "role": "top", "root": {"elev": 76, "az": az},
                            "tip": {"elev": 50, "az": az}, "hang_to_y": None, "length": 0.0,
                            "width": [0.016, 0.032, 0.014], "thickness": [0.004, 0.006, 0.002],
                            "clear": 0.0025, "bend": 0.003, "layer": 0.0})
    for i, lk in enumerate(sorted((lk for lk in bp["locks"] if lk["role"] == "top"), key=lambda lk: lk["root"]["az"] % 360)):
        lk["shell"], lk["layer"] = ("outer", 0.003) if i % 2 else ("inner", 0.0)
    ax = bp["head"]["semi_axes_xyz"]
    for lk in bp["locks"]:
        lk["registry"] = B3.registry(ax, lk)
        if lk["role"] == "top":
            lk["length"] = round(lk["registry"]["arc_length_spine"], 4)  # design length = design spine arc
    bp["layers"]["top"] = "12-lock whorl from elev 76 to 50 (covers crown and frontal scalp), inner/outer 0 / 3 mm"
    bp["targets"]["min_head_clearance"] = {"value": 0.0025, "tolerance": 0.0014,
                                           "note": "whorl clear 2.5 mm sits above the 1.5 mm-lifted crown fill"}
    bp["derived_from"] = "qual_hair_blueprint_v3.json"
    (HERE / "qual_hair_blueprint_v4.json").write_text(json.dumps(bp, indent=1, ensure_ascii=False) + "\n")
    print(len(bp["locks"]), "locks")


if __name__ == "__main__":
    main()
