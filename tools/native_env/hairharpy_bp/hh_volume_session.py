#!/usr/bin/env python3
"""v2 volumetric hair session on the #468 shared controller (pin 8c1d5ae; isolated fencing remote, no production lease).

Stages: hh_base (HairHarpy base: head + crown + continuation; reused code from hh_session)
        hhv_op_qualify (measured gains of the len / w / t controls on every lock; cross-coupling recorded)
        hhv_locks (factory: edit -> measure -> correct -> finish (NPR, strand UV, matched + face renders) -> reopen)
Cross-run restore is reused from the qualified v1 session (runs 45081346528 / 45081761275); not repeated here.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hh_native as H  # noqa: E402
import hh_volume as V  # noqa: E402
from hh_session import ASSET, REMOTE, Session, git, sha  # noqa: E402
from hh_volume_adapter import METRICS, MEASURE_ID, OPERATION_ID, SCOPE_ID, VolumeAdapter, design_values, tolerances  # noqa: E402


class VSession(Session):
    def persist(self, records, token, deadline):
        from shared_asset_lease import publish_checkpoint
        (self.root / "ledger.json").write_text(json.dumps(records, indent=1, sort_keys=True))
        git(self.root, "add", "-A", "ckpt", "ledger.json")
        for r in records.values():
            for p in [r["path"]] + list(r.get("files", {})):
                git(self.root, "add", "-f", p)
        git(self.root, "commit", "-q", "--allow-empty", "-m", "checkpoint " + ",".join(sorted(records)))
        cur = git(self.root, "rev-parse", "HEAD")
        nxt = publish_checkpoint(REMOTE, ASSET, token, cur, self.previous)
        self.previous = cur
        self.log("persist", checkpoint=cur, stages=sorted(records))
        return nxt

    def ex_qualify_v2(self, stage, token, deadline):
        base = self.root / self.completed["hh_base"]["path"]
        w = self.root / "work" / "qualify_v2"
        w.mkdir(parents=True, exist_ok=True)
        bp = json.loads(self.bp_path.read_text())
        ad = VolumeAdapter(self.bp_path, self.a.blender, self.a.display, {}, w, str(self.root / "ckpt" / "qual_head.obj"))
        steps = {"base": None, "len": None, "w": 0.15, "t": 0.15}
        res = {}
        for name in steps:
            nat = w / f"q_{name}.hairmesh"
            shutil.copyfile(base, nat)
            ctl = V.default_controls(bp)
            if name != "base":
                for lk in bp["locks"]:
                    ctl[lk["id"]][name] += (-4.0 if lk.get("hang_to_y") is None else -0.02) if name == "len" else steps[name]
            ad.apply(nat, ctl, deadline, f"q_{name}")
            res[name] = (ctl, ad.measure_raw(nat, deadline, f"q_{name}_m")[0])
        gains, coupling, ok = {}, {}, True
        for lk in bp["locks"]:
            k = lk["id"]
            gains[k], coupling[k] = {}, {}
            for metric, c, _ in METRICS:
                dx = res[c][0][k][c] - res["base"][0][k][c]
                dy = res[c][1]["locks"][k][metric] - res["base"][1]["locks"][k][metric]
                gains[k][c] = dy / dx
                exp = {"len": -1.0 if lk.get("hang_to_y") is not None else -0.0012, "w": lk["width"][1], "t": lk["thickness"][1]}[c]
                good = gains[k][c] * exp > 0 and abs(gains[k][c]) > 0.3 * abs(exp)
                ok &= good
                # cross-coupling: what this control does to the other two metrics
                coupling[k][c] = {m2: res[c][1]["locks"][k][m2] - res["base"][1]["locks"][k][m2] for m2, c2, _ in METRICS if c2 != c}
        ev = {"operation_id": OPERATION_ID, "controls": {"len": "bangs: tip elevation (deg); hanging: hang end y (m)",
                                                        "w": "width profile scale", "t": "thickness profile scale"},
              "steps": {"len": "-4 deg / -0.02 m", "w": "+0.15", "t": "+0.15"}, "gains": gains, "coupling": coupling,
              "qualified": ok, "criteria": "same sign as the geometric expectation and |gain| > 0.3 x expectation",
              "base_measure": res["base"][1]["locks"], "structure_base": res["base"][1]["structure"]}
        out = self.root / "ckpt" / "hhv_op_response.json"
        out.write_text(json.dumps(ev, indent=1, sort_keys=True))
        self.log("op_qualify_v2", qualified=ok, gains={k: {c: round(v, 5) for c, v in g.items()} for k, g in gains.items()})
        if not ok:
            raise RuntimeError("v2 operation responses not qualified")
        return {"path": out.relative_to(self.root).as_posix(), "sha256": sha(out), "reopened": True,
                "fingerprint": stage["fingerprint"]}

    def target_v2(self, base_rec, resp_rec):
        from shared_blueprint_contract import digest_record
        bp = json.loads(self.bp_path.read_text())
        values = design_values(bp)
        deps = {"hh_base": base_rec["sha256"], "hhv_op_qualify": resp_rec["sha256"]}
        target = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "sha256": sha(self.bp_path),
                  "coordinate_system": bp["coordinate_system"], "units": bp["units"], "projection": bp["projection"],
                  "measurement_id": MEASURE_ID, "values": values, "tolerances": tolerances(bp),
                  "uncertainty": {k: 0.0 for k in values},
                  "operation": {"id": OPERATION_ID, "qualified": True, "evidence_sha256": resp_rec["sha256"]},
                  "protection": {"scope_id": SCOPE_ID, "baseline_sha256": base_rec["protected_sha256"]},
                  "dependency_fingerprint": digest_record(deps)}
        request = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "reference_sha256": sha(self.bp_path),
                   "dependency_hashes": deps, "asset_id": ASSET, "head_sha": None, "stage": "hhv_locks"}
        return target, request


def main():
    ap = argparse.ArgumentParser()
    for k in ("root", "engine", "blueprint", "blender", "display", "head", "hh_sha", "blender_version"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, required=True)
    ap.add_argument("--budget", type=float, default=19800)
    ap.add_argument("--reserve", type=float, default=900)
    a = ap.parse_args()
    a.mode = "v2"
    s = VSession(a)
    s.previous = None
    root = s.root
    summary = {"mode": "v2", "asset": ASSET, "lease": "ISOLATED git remote inside the session root (not production)"}
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
        f_q = s.fp("hhv_op_qualify", {}, {"hh_base": f_base})
        f_l = s.fp("hhv_locks", {}, {"hh_base": f_base, "hhv_op_qualify": f_q})
        st = [dict(id="hh_base", deps=[], seconds=600, qualified=True, fingerprint=f_base),
              dict(id="hhv_op_qualify", deps=["hh_base"], seconds=2400, qualified=True, fingerprint=f_q)]

        def execute(stage, token, deadline):
            return {"hh_base": s.ex_base, "hhv_op_qualify": s.ex_qualify_v2}[stage["id"]](stage, token, deadline)
        summary["pass1_executed"] = s.run_pass(st, execute)
        resp = json.loads((root / s.completed["hhv_op_qualify"]["path"]).read_text())
        target, request = s.target_v2(s.completed["hh_base"], s.completed["hhv_op_qualify"])
        adapter = VolumeAdapter(s.bp_path, a.blender, a.display, resp["gains"], root / "work" / "locks",
                                str(root / "ckpt" / "qual_head.obj"))
        st2 = st + [dict(id="hhv_locks", deps=["hh_base"], seconds=5400, qualified=True, fingerprint=f_l, requires_blueprint=True)]
        from shared_asset_lease import acquire
        from shared_session_controller import run
        os.chdir(root)
        commit = git(root, "rev-parse", "HEAD")
        request["head_sha"] = commit
        summary["pass2_executed"] = run(REMOTE, ASSET, commit, root, st2, s.completed, execute, s.persist,
                                        budget=a.budget, reserve=a.reserve, reservation=acquire(REMOTE, ASSET, commit),
                                        fenced=True, blueprint_targets={"hhv_locks": (target, request)},
                                        factory_stages={"hhv_locks": (None, adapter)})
        rec = s.completed["hhv_locks"]
        summary["locks_record"] = {k: v for k, v in rec.items() if k != "observation"}
        summary["final_observation"] = rec["observation"]
        summary["adapter_history"] = adapter.history
        summary["gains"] = resp["gains"]
        summary["target"] = target
        summary["status"] = "COMPLETE"
    except BaseException as e:
        summary["status"] = "FAILED"
        summary["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        summary["events"] = s.events
        (root.parent / "hhv_session_summary.json").write_text(json.dumps(summary, indent=1, default=str))
        print("TWO_HHV_SESSION_SUMMARY", summary["status"], summary.get("error", ""))


if __name__ == "__main__":
    main()
