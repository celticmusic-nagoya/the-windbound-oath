"""MORWEN-EYES-LIDS-MOUTH-04: reproducible evidence for the STOPPED annulus-ring retopology method.

Builds the lid R / lid L / mouth annulus patches on the locked #312 nose (depth 0.5) for each
configuration in elm_params_04.json["trial_configs"] and reports winding conflicts, UV-orientation
flips and geometric folds (adjacent dihedral > 120 deg with a face pointing away from its
neighbours) per patch, against the same counts on the original region. In-memory only; nothing
from this trial goes into the candidate.
"""
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent


def _load(path, name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


E = _load(HERE / "build_eyes_lids_mouth_04.py", "morwen_elm_build")
R = _load(HERE.parent / "nose_retopo" / "run_nose_retopo_03.py", "morwen_nose_run")
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyes_lids_mouth_04"))


def counts(face, verts):
    me = face.data
    si = E.M3.slot_index(face, "Face_00_SKIN")
    uvl = me.uv_layers.active.data

    def ua(p):
        u = [uvl[li].uv for li in p.loop_indices]
        return sum(u[i].x * u[(i + 1) % len(u)].y - u[(i + 1) % len(u)].x * u[i].y for i in range(len(u))) / 2
    skin = [p for p in me.polygons if p.material_index == si]
    sign = np.sign(np.median([ua(p) for p in skin if not any(v in verts for v in p.vertices)]))
    pp = [p for p in skin if any(v in verts for v in p.vertices)]
    adj = {}
    for p in pp:
        for ek in p.edge_keys:
            adj.setdefault(ek, []).append(p)
    folds = 0
    for p in pp:
        worst = max((math.degrees(p.normal.angle(q.normal)) for ek in p.edge_keys for q in adj[ek] if q.index != p.index), default=0)
        folds += worst > 120
    return {"faces": len(pp), "winding_conflicts": R.winding_conflicts(face, verts),
            "uv_orientation_flips": sum(1 for p in pp if np.sign(ua(p)) != sign), "folded_faces": folds}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P = json.loads(E.PARAMS_PATH.read_text())
    res = {"method_family": P["retopo_status"]["method_family"], "configs": {}}
    for cfg in P["trial_configs"]:
        E.M3.load()
        nrec = E.build_base(P)
        face = bpy.data.objects["Face"]
        L = nrec["baseline"]["landmarks"]
        ells = E.ellipses(P, L)
        base = {n: counts(face, E.region_vertices(face, n, spec)) for n, spec in ells.items()}
        si = E.M3.slot_index(face, "Face_00_SKIN")
        out = {}
        for (name, (key, ell, sp)), pid in zip(ells.items(), (1, 2, 3)):
            E.build_annulus(face, si, key, ell, sp["ring_t"], sp["notch_ratio"], pid,
                            sp.get("membership", "all_vertices"), cfg["relax_iterations"])
            attr = face.data.attributes[E.PATCH_ATTR].data
            out[name] = {"original_region": base[name],
                         "patch": counts(face, {i for i, a in enumerate(attr) if a.value == pid})}
        out["verdict"] = ("FAIL" if any(out[n]["patch"]["folded_faces"] > out[n]["original_region"]["folded_faces"]
                                        or out[n]["patch"]["uv_orientation_flips"] > out[n]["original_region"]["uv_orientation_flips"]
                                        for n in ells) else "PASS")
        res["configs"][cfg["name"]] = out
    (OUT / "ANNULUS_RETOPO_TRIAL.json").write_text(json.dumps(res, indent=2) + "\n")
    print("annulus trial:", {k: v["verdict"] for k, v in res["configs"].items()})


if __name__ == "__main__":
    main()
