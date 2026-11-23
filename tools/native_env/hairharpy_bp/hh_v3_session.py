#!/usr/bin/env python3
"""v3 hair session (#468 8c1d5ae, isolated fencing remote): top cover layer, layered placement, design registry
targets (length / width / thickness / curvature / taper / penetration). Reuses hh_base and the v2 session plumbing.
"""
import argparse
import json
import os
import shutil
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hh_volume as V  # noqa: E402
from hh_session import ASSET, REMOTE, git, sha  # noqa: E402
from hh_v3_adapter import CORRECTED, MEASURE_ID, OPERATION_ID, V3Adapter, design_values, tolerances  # noqa: E402
from hh_volume_adapter import SCOPE_ID  # noqa: E402
from hh_volume_session import VSession  # noqa: E402

STEPS = {"len": None, "w": 0.15, "t": 0.15, "bend": 0.006, "tipw": 0.4}


class V3Session(VSession):
    def ex_qualify_v3(self, stage, token, deadline):
        base = self.root / self.completed["hh_base"]["path"]
        w = self.root / "work" / "qualify_v3"
        w.mkdir(parents=True, exist_ok=True)
        bp = json.loads(self.bp_path.read_text())
        ad = V3Adapter(self.bp_path, self.a.blender, self.a.display, {}, w, str(self.root / "ckpt" / "qual_head.obj"))
        runs = {}
        for name in ["base"] + list(STEPS) + ["layer"]:
            nat = w / f"q_{name}.hairmesh"
            shutil.copyfile(base, nat)
            ctl = V.default_controls(bp)
            for i, lk in enumerate(bp["locks"]):
                c = ctl[lk["id"]]
                if name == "len":
                    c["len"] += -4.0 if lk.get("hang_to_y") is None else -0.02
                elif name == "layer":
                    c["layer"] += 0.012 if lk.get("shell") == "outer" else 0.0  # raise the shell the correction raises
                elif name in STEPS:
                    c[name] += STEPS[name]
            ad.apply(nat, ctl, deadline, f"q_{name}")
            runs[name] = (ctl, ad.measure_raw(nat, deadline, f"q_{name}_m")[0])
        b_ctl, b_m = runs["base"]
        gains, coupling, ok, bad = {}, {}, True, []
        for lk in bp["locks"]:
            k = lk["id"]
            gains[k], coupling[k] = {}, {}
            for metric, c, _ in CORRECTED:
                ctl, m = runs[c]
                g = (m["locks"][k][metric] - b_m["locks"][k][metric]) / (ctl[k][c] - b_ctl[k][c])
                gains[k][c] = g
                sign = -1 if c == "len" else 1
                if not (g * sign > 0 and abs(g) > 1e-6):
                    bad.append(f"{k}:{c}")
                    gains[k][c] = None  # not qualified for this lock: metric is checked, never corrected
                    if c in ("len", "w", "t"):
                        ok = False
                coupling[k][c] = {m2: m["locks"][k][m2] - b_m["locks"][k][m2] for m2, c2, _ in CORRECTED if c2 != c}
        # layer (separation) operation: nonlinear (depth falls only once the raise approaches the lock thickness), so it
        # is qualified as monotonic, not as a linear gain; correction steps by the measured depth + margin and re-measures
        lc, lm = runs["layer"]
        bp0, lp0 = b_m["penetration"], lm["penetration"]
        shell = {lk["id"]: lk.get("shell") for lk in bp["locks"]}

        def cross(pen):  # inner/outer shell pairs: the pairs the raise is meant to separate
            ps = [p for p in pen.get("pairs", []) if p["class"] == "penetration" and {shell[p["a"]], shell[p["b"]]} == {"inner", "outer"}]
            return len({tuple(sorted((p["a"], p["b"]))) for p in ps}), max([p["max_depth"] for p in ps] or [0.0])
        (bn, bd), (ln, ld) = cross(bp0), cross(lp0)
        lg = {"base_pairs": bp0["penetration_pairs"], "raised_pairs": lp0["penetration_pairs"],
              "base_max_depth": bp0["max_penetration_depth"], "raised_max_depth": lp0["max_penetration_depth"],
              "cross_shell_pairs": [bn, ln], "cross_shell_max_depth": [bd, ld], "step_m": 0.012, "raised": "outer shell"}
        gains["_layer"] = -1.0  # step policy: raise by (depth + 0.8 mm) per iteration
        ok &= ln < bn and ld <= bd
        ev = {"operation_id": OPERATION_ID, "steps": dict(STEPS, len="-4 deg / -0.02 m", layer="+12 mm on outer-shell locks"),
              "gains": gains, "coupling": coupling, "layer_samples": lg, "qualified": ok, "not_qualified": bad,
              "criteria": "sign of each gain matches its geometric expectation (len/w/t required for every lock; bend/tipw excluded per lock where not); layer: inner/outer-shell penetration pairs and their max depth fall for a 12 mm outer-shell raise",
              "base_measure": b_m["locks"], "base_penetration": {k: v for k, v in b_m["penetration"].items() if k != "pairs"},
              "base_structure": b_m["structure"]}
        out = self.root / "ckpt" / "hhv3_op_response.json"
        out.write_text(json.dumps(ev, indent=1, sort_keys=True))
        self.log("op_qualify_v3", qualified=ok, not_qualified=bad, layer=lg)
        if not ok:
            raise RuntimeError("v3 operation responses not qualified: " + ",".join(bad))
        return {"path": out.relative_to(self.root).as_posix(), "sha256": sha(out), "reopened": True,
                "fingerprint": stage["fingerprint"]}

    def target_v3(self, base_rec, resp_rec):
        from shared_blueprint_contract import digest_record
        bp = json.loads(self.bp_path.read_text())
        values = design_values(bp)
        deps = {"hh_base": base_rec["sha256"], "hhv3_op_qualify": resp_rec["sha256"]}
        target = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "sha256": sha(self.bp_path),
                  "coordinate_system": bp["coordinate_system"], "units": bp["units"], "projection": bp["projection"],
                  "measurement_id": MEASURE_ID, "values": values, "tolerances": tolerances(bp),
                  "uncertainty": {k: 0.0 for k in values},
                  "operation": {"id": OPERATION_ID, "qualified": True, "evidence_sha256": resp_rec["sha256"]},
                  "protection": {"scope_id": SCOPE_ID, "baseline_sha256": base_rec["protected_sha256"]},
                  "dependency_fingerprint": digest_record(deps)}
        request = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "reference_sha256": sha(self.bp_path),
                   "dependency_hashes": deps, "asset_id": ASSET, "head_sha": None, "stage": "hhv3_locks"}
        return target, request


def main():
    ap = argparse.ArgumentParser()
    for k in ("root", "engine", "blueprint", "blender", "display", "head", "hh_sha", "blender_version"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, required=True)
    ap.add_argument("--budget", type=float, default=19800)
    ap.add_argument("--reserve", type=float, default=900)
    a = ap.parse_args()
    a.mode = "v3"
    s = V3Session(a)
    s.previous = None
    root = s.root
    summary = {"mode": "v3", "asset": ASSET, "lease": "ISOLATED git remote inside the session root (not production)"}
    try:
        root.mkdir(parents=True)
        for c in (("init", "-q"), ("config", "user.name", "TWO session"), ("config", "user.email", "session@invalid"),
                  ("init", "--bare", "-q", REMOTE)):
            git(root, *c)
        (root / ".gitignore").write_text("isolated.git/\nwork/\n")
        (root / "ckpt").mkdir()
        shutil.copyfile(a.head, root / "ckpt" / "qual_head.obj")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "session start")
        s.completed = {}
        f_base = s.fp("hh_base", {"head": sha(root / "ckpt" / "qual_head.obj")}, {})
        f_q = s.fp("hhv3_op_qualify", {}, {"hh_base": f_base})
        f_l = s.fp("hhv3_locks", {}, {"hh_base": f_base, "hhv3_op_qualify": f_q})
        st = [dict(id="hh_base", deps=[], seconds=600, qualified=True, fingerprint=f_base),
              dict(id="hhv3_op_qualify", deps=["hh_base"], seconds=3600, qualified=True, fingerprint=f_q)]

        def execute(stage, token, deadline):
            return {"hh_base": s.ex_base, "hhv3_op_qualify": s.ex_qualify_v3}[stage["id"]](stage, token, deadline)
        summary["pass1_executed"] = s.run_pass(st, execute)
        resp = json.loads((root / s.completed["hhv3_op_qualify"]["path"]).read_text())
        target, request = s.target_v3(s.completed["hh_base"], s.completed["hhv3_op_qualify"])
        adapter = V3Adapter(s.bp_path, a.blender, a.display, resp["gains"], root / "work" / "locks", str(root / "ckpt" / "qual_head.obj"))
        st2 = st + [dict(id="hhv3_locks", deps=["hh_base"], seconds=7200, qualified=True, fingerprint=f_l, requires_blueprint=True)]
        from shared_asset_lease import acquire
        from shared_session_controller import run
        os.chdir(root)
        commit = git(root, "rev-parse", "HEAD")
        request["head_sha"] = commit
        summary["pass2_executed"] = run(REMOTE, ASSET, commit, root, st2, s.completed, execute, s.persist, budget=a.budget,
                                        reserve=a.reserve, reservation=acquire(REMOTE, ASSET, commit), fenced=True,
                                        blueprint_targets={"hhv3_locks": (target, request)},
                                        factory_stages={"hhv3_locks": (None, adapter)})
        rec = s.completed["hhv3_locks"]
        summary.update(locks_record={k: v for k, v in rec.items() if k != "observation"}, final_observation=rec["observation"],
                       adapter_history=adapter.history, gains=resp["gains"], target=target, status="COMPLETE")
    except BaseException as e:
        summary["status"] = "FAILED"
        summary["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        summary["events"] = s.events
        (root.parent / "hhv3_session_summary.json").write_text(json.dumps(summary, indent=1, default=str))
        print("TWO_HHV3_SESSION_SUMMARY", summary["status"], summary.get("error", ""))


if __name__ == "__main__":
    main()
