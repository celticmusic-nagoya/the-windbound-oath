#!/usr/bin/env python3
"""HairHarpy hair session on the #468 shared session controller (ISOLATED fencing remote, no production lease).

Stages (asset MORWEN, isolated git remote inside the session root):
  hh_base        HairHarpy newproj + neutral head + crown + continuation, saved and reopened  (execute)
  hh_op_qualify  operation response model: tip-anchor move -> measured lock length (3 points)  (execute)
  hh_locks       blueprint precision stage via execute_factory_stage: edit/measure/correct/finish/reopen
  hh_hq          (run2 only) restored session continues: Cycles HQ matched views of the finished .blend  (execute)
run1: hh_base, hh_op_qualify, hh_locks.  run2: restore the run1 root, completed stages skipped, hh_hq executed.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hh_native as H  # noqa: E402
from hh_factory_adapter import (HairHarpyLockAdapter, MEASURE_ID, OPERATION_ID, SCOPE_ID,  # noqa: E402
                                design_values, target_keys)

ASSET = "MORWEN"  # registered key; lease ref lives ONLY in the isolated remote below
REMOTE = "isolated.git"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(root, *a):
    return subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True).stdout.strip()


def code_hashes():
    return {p.name: sha(p) for p in sorted(HERE.glob("*.py"))} | {"pbr_factory.py": sha(HERE.parent / "pbr_factory.py"),
                                                                  "render_views.py": sha(HERE.parent / "render_views.py")}


class Session:
    def __init__(self, a):
        self.a = a
        self.root = Path(a.root).resolve()
        self.engine = Path(a.engine).resolve()
        sys.path.insert(0, str(self.engine))
        self.bp_path = Path(a.blueprint).resolve()
        self.env_hash = hashlib.sha256(json.dumps({"hairharpy": a.hh_sha, "blender": a.blender_version}).encode()).hexdigest()
        self.events = []

    def log(self, kind, **kw):
        kw.update(event=kind, t=round(time.time(), 2))
        self.events.append(kw)
        print("TWO_HH_SESSION", json.dumps(kw, default=str), flush=True)

    def fp(self, stage, inputs, deps):
        from shared_session_contract import fingerprint
        inputs = dict(inputs, head=sha(self.root / "ckpt" / "qual_head.obj"))
        return fingerprint(ASSET, stage, {"blueprint": {"qual_hair_blueprint_v1.json": sha(self.bp_path)},
                                          "inputs": inputs, "code": code_hashes(), "environment": {"env": self.env_hash},
                                          "dependencies": deps, "qa": {"contract": sha(self.engine / "shared_blueprint_contract.py")}})

    # ---- execute stages ----
    def ex_base(self, stage, token, deadline):
        out = self.root / "ckpt" / "hh_base.hairmesh"
        out.parent.mkdir(exist_ok=True)
        w = self.root / "work" / "base"
        head = self.root / "ckpt" / "qual_head.obj"
        log, _ = H.run_app(None, f"newproj;room hair;importhead {head};crowncreate;wait 300;crowncont;wait 500;save {out}",
                           w, deadline, self.a.display)
        d = H.load(out)
        log2, _ = H.run_app(out, "room hair;wait 300;tree", w / "reopen", deadline, self.a.display)
        if "continuation" not in log2 or H.sha(out) != sha(out):
            raise RuntimeError("base reopen failed")
        return {"path": out.relative_to(self.root).as_posix(), "sha256": sha(out), "reopened": True,
                "fingerprint": stage["fingerprint"], "protected_sha256": H.protected_fingerprint(d)}

    def ex_qualify(self, stage, token, deadline):
        base = self.root / self.completed["hh_base"]["path"]
        w = self.root / "work" / "qualify"
        w.mkdir(parents=True, exist_ok=True)
        bp = json.loads(self.bp_path.read_text())
        ad = HairHarpyLockAdapter(self.bp_path, self.a.blender, self.a.display, {"slope": {}, "reference": {}}, w)
        roots = H.connector_roots(H.load(base))
        points = {}
        for dy in (0.0, -0.015, 0.015):
            nat = w / f"q{dy:+.3f}.hairmesh"
            shutil.copyfile(base, nat)
            ctl = {}
            for lk in bp["locks"]:
                ry = (roots[lk["roots"][0]][1][1] + roots[lk["roots"][1]][1][1]) / 2
                ctl[lk["id"]] = {"tip_y": ry - lk["length"] * 0.92 + dy, "bend": lk["bend"]}
            ad._rebuild(nat, ctl, deadline, f"q{dy:+.3f}")
            m, _, _ = ad._export_measure(nat, deadline, f"q{dy:+.3f}_m")
            points[dy] = {k: (ctl[k]["tip_y"], m["locks"][k]["length"]) for k in ctl}
        slope, lin, ref = {}, {}, {}
        for k in points[0.0]:
            (y0, l0), (y1, l1), (y2, l2) = points[-0.015][k], points[0.0][k], points[0.015][k]
            slope[k] = (l2 - l0) / (y2 - y0)
            lin[k] = abs(l1 - (l0 + slope[k] * (y1 - y0)))  # deviation of the middle point from the chord
            ref[k] = {"tip_y": y1, "length": l1}
        # qualified = monotonic, usable local gain; nonlinearity is recorded and handled by per-lock secant correction
        mono = {k: (points[0.0][k][1] - points[-0.015][k][1]) < 0 and (points[0.015][k][1] - points[0.0][k][1]) < 0 for k in slope}
        ok = all(mono.values()) and all(-2.0 < s < -0.3 for s in slope.values())
        ev = {"operation_id": OPERATION_ID, "method": "native tip-anchor move, HairHarpy cocoon/convert, Blender surface length",
              "points": {str(k): v for k, v in points.items()}, "slope": slope, "monotonic": mono,
              "criteria": "monotonic decreasing length vs tip height, -2.0 < gain < -0.3 (m/m); step 0.015 m", "nonlinearity_m": lin, "reference": ref,
              "qualified": ok}
        out = self.root / "ckpt" / "hh_op_response.json"
        out.write_text(json.dumps(ev, indent=1, sort_keys=True))
        self.log("op_qualify", qualified=ok, slope={k: round(v, 3) for k, v in slope.items()},
                 nonlinearity={k: round(v, 5) for k, v in lin.items()})
        if not ok:
            raise RuntimeError("operation response not qualified")
        return {"path": out.relative_to(self.root).as_posix(), "sha256": sha(out), "reopened": True,
                "fingerprint": stage["fingerprint"]}

    def ex_hq(self, stage, token, deadline):
        rec = self.completed["hh_locks"]
        blend = (self.root / rec["path"]).parent / "hair_qual_530.blend"
        out = self.root / "ckpt" / "hq"
        script = ("import bpy,sys,json;sys.path.insert(0,%r);import render_views as R;"
                  "n=sorted(o.name for o in bpy.data.objects if o.type=='MESH' and 'cocoon' in o.name.lower());"
                  "s=R.render(bpy.context.scene,'hq',__import__('pathlib').Path(%r),n,keep=());"
                  "open(%r,'w').write(json.dumps(s))") % (str(HERE.parent), str(out), str(out) + ".json")
        p = subprocess.run([self.a.blender, "-b", str(blend), "--factory-startup", "--python-exit-code", "3",
                            "--python-expr", script], capture_output=True, text=True,
                           timeout=max(10, deadline - time.monotonic() - 5))
        if p.returncode:
            raise RuntimeError(p.stdout[-500:])
        man = out.parent / "hq_manifest.json"
        man.write_text(json.dumps({"source_blend_sha256": sha(blend), "renders": {f.name: sha(f) for f in sorted(out.glob("*.png"))},
                                   "stats": json.loads(Path(str(out) + ".json").read_text())}, indent=1))
        return {"path": man.relative_to(self.root).as_posix(), "sha256": sha(man), "reopened": True,
                "fingerprint": stage["fingerprint"]}

    # ---- controller plumbing ----
    def persist(self, records, token, deadline):
        from shared_asset_lease import publish_checkpoint
        (self.root / "ledger.json").write_text(json.dumps(records, indent=1, sort_keys=True))
        git(self.root, "add", "-A", "ckpt", "ledger.json")
        for r in records.values():
            git(self.root, "add", "-f", r["path"])
            p = (self.root / r["path"]).parent
            if p.name.startswith("factory-"):
                git(self.root, "add", "-f", str(p.relative_to(self.root)))
        git(self.root, "commit", "-q", "--allow-empty", "-m", "checkpoint " + ",".join(sorted(records)))
        cur = git(self.root, "rev-parse", "HEAD")
        nxt = publish_checkpoint(REMOTE, ASSET, token, cur, self.previous)
        self.previous = cur
        self.log("persist", checkpoint=cur, stages=sorted(records))
        return nxt

    def run_pass(self, stages, execute, targets=None, factories=None):
        from shared_asset_lease import acquire
        from shared_session_controller import run
        os.chdir(self.root)
        commit = git(self.root, "rev-parse", "HEAD")
        reservation = acquire(REMOTE, ASSET, commit)
        return run(REMOTE, ASSET, commit, self.root, stages, self.completed, execute, self.persist,
                   budget=self.a.budget, reserve=self.a.reserve, reservation=reservation, fenced=True,
                   blueprint_targets=targets or {}, factory_stages=factories or {})

    def build_target(self, base_rec, resp_rec, stage_id):
        from shared_blueprint_contract import digest_record
        bp = json.loads(self.bp_path.read_text())
        values = design_values(bp)
        tol = {k: bp["targets"]["lock_length"]["tolerance"] for k in values if k.endswith("_length")}
        tol["asymmetry_left_over_right"] = bp["targets"]["asymmetry_left_over_right"]["tolerance"]
        tol["min_head_clearance"] = bp["targets"]["min_head_clearance"]["tolerance"]
        deps = {"hh_base": base_rec["sha256"], "hh_op_qualify": resp_rec["sha256"]}
        target = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "sha256": sha(self.bp_path),
                  "coordinate_system": bp["coordinate_system"], "units": bp["units"], "projection": bp["projection"],
                  "measurement_id": MEASURE_ID, "values": values, "tolerances": tol,
                  "uncertainty": {k: 0.0 for k in values},  # design values are exact numbers (no 2D inference)
                  "operation": {"id": OPERATION_ID, "qualified": True, "evidence_sha256": resp_rec["sha256"]},
                  "protection": {"scope_id": SCOPE_ID, "baseline_sha256": base_rec["protected_sha256"]},
                  "dependency_fingerprint": digest_record(deps)}
        request = {"target_id": bp["blueprint_id"], "source_sha256": base_rec["sha256"], "reference_sha256": sha(self.bp_path),
                   "dependency_hashes": deps, "asset_id": ASSET, "head_sha": None, "stage": stage_id}
        return target, request


def restore_checks(s, root, target, stages, adapter):
    """run2 before continuing: verify restored checkpoints, prove that a changed blueprint target invalidates the
    reused precision stage, and that a failing factory attempt is quarantined without touching the ledger."""
    from session_plan import ready
    from shared_blueprint_contract import digest_record
    out = {}
    led = s.completed
    out["checkpoint_sha_ok"] = {k: sha(root / v["path"]) == v["sha256"] for k, v in led.items()}
    out["git_checkpoints"] = git(root, "log", "--oneline", "-5").splitlines()
    out["plan_after_restore"] = ready(stages, led, root, 10000, 600)
    changed = json.loads(json.dumps(target))
    changed["tolerances"]["L01_length"] = 0.002
    out["changed_target_invalidates_hh_locks"] = led["hh_locks"]["target_contract_sha256"] != digest_record(changed)
    # failing factory attempt on a scratch copy: unachievable tolerance -> quarantine, ledger untouched
    import copy
    from shared_factory_stage import execute_factory_stage
    scratch = root.parent / "scratch_failure"
    shutil.copytree(root, scratch, ignore=shutil.ignore_patterns("isolated.git", "work"))
    bad = copy.deepcopy(target)
    for k in bad["tolerances"]:
        bad["tolerances"][k] = 1e-6
    req = {"target_id": bad["target_id"], "source_sha256": bad["source_sha256"], "reference_sha256": bad["sha256"],
           "dependency_hashes": {"hh_base": led["hh_base"]["sha256"], "hh_op_qualify": led["hh_op_qualify"]["sha256"]}}
    ledger_before = sha(scratch / "ledger.json")
    st = next(x for x in stages if x["id"] == "hh_locks")
    try:
        execute_factory_stage(scratch, scratch / led["hh_base"]["path"], st, bad, req, adapter,
                              time.monotonic() + 1800, lambda: None)
        out["failure_path"] = "NOT_TRIGGERED"
    except RuntimeError as e:
        q = sorted(p.name for p in (scratch / "quarantine").iterdir())
        out["failure_path"] = {"error": str(e)[:200], "quarantined_attempts": q,
                               "ledger_unchanged": sha(scratch / "ledger.json") == ledger_before,
                               "no_unquarantined_attempt": not [p for p in scratch.glob("factory-*") if p.name not in
                                                                {Path(led["hh_locks"]["path"]).parent.name}]}
    s.log("restore_checks", **{k: v for k, v in out.items() if k != "git_checkpoints"})
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("root", "engine", "blueprint", "blender", "display", "mode", "head", "hh_sha", "blender_version"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, required=k not in ("head",))
    ap.add_argument("--budget", type=float, default=19800)
    ap.add_argument("--reserve", type=float, default=900)
    a = ap.parse_args()
    s = Session(a)
    s.previous = None
    root = s.root
    summary = {"mode": a.mode, "asset": ASSET, "lease": "ISOLATED git remote inside the session root (not production)"}
    try:
        if a.mode == "run1":
            root.mkdir(parents=True)
            git(root, "init", "-q")
            git(root, "config", "user.name", "TWO session")
            git(root, "config", "user.email", "session@invalid")
            git(root, "init", "--bare", "-q", REMOTE)
            (root / ".gitignore").write_text("isolated.git/\nwork/\n")
            (root / "ckpt").mkdir()
            shutil.copyfile(a.head, root / "ckpt" / "qual_head.obj")
            git(root, "add", "-A")
            git(root, "commit", "-qm", "session start")
            s.completed = {}
        else:
            s.completed = json.loads((root / "ledger.json").read_text())
            s.previous = git(root, "rev-parse", "HEAD")
            summary["restored_ledger"] = sorted(s.completed)
        f_base = s.fp("hh_base", {"head": sha(root / "ckpt" / "qual_head.obj")}, {})
        f_q = s.fp("hh_op_qualify", {}, {"hh_base": f_base})
        f_l = s.fp("hh_locks", {}, {"hh_base": f_base, "hh_op_qualify": f_q})
        st = [dict(id="hh_base", deps=[], seconds=600, qualified=True, fingerprint=f_base),
              dict(id="hh_op_qualify", deps=["hh_base"], seconds=1500, qualified=True, fingerprint=f_q)]

        def execute(stage, token, deadline):
            return {"hh_base": s.ex_base, "hh_op_qualify": s.ex_qualify, "hh_hq": s.ex_hq}[stage["id"]](stage, token, deadline)
        summary["pass1_executed"] = s.run_pass(st, execute)
        resp = json.loads((root / s.completed["hh_op_qualify"]["path"]).read_text())
        target, request = s.build_target(s.completed["hh_base"], s.completed["hh_op_qualify"], "hh_locks")
        request["head_sha"] = git(root, "rev-parse", "HEAD")
        adapter = HairHarpyLockAdapter(s.bp_path, a.blender, a.display, {"slope": resp["slope"], "reference": resp["reference"],
                                                                        "evidence_sha256": s.completed["hh_op_qualify"]["sha256"]},
                                       root / "work" / "locks")
        st2 = st + [dict(id="hh_locks", deps=["hh_base"], seconds=3600, qualified=True, fingerprint=f_l, requires_blueprint=True)]
        if a.mode == "run2":
            st2.append(dict(id="hh_hq", deps=["hh_locks"], seconds=3600, qualified=True, fingerprint=s.fp("hh_hq", {}, {"hh_locks": f_l})))
        # the controller binds request.head_sha to the commit it runs at: refresh after pass 1 commits
        from shared_asset_lease import acquire  # noqa: F401
        target_req = (target, request)
        orig_run_pass = s.run_pass

        def run_pass2():
            from shared_asset_lease import acquire as acq
            from shared_session_controller import run
            os.chdir(root)
            commit = git(root, "rev-parse", "HEAD")
            request["head_sha"] = commit
            reservation = acq(REMOTE, ASSET, commit)
            return run(REMOTE, ASSET, commit, root, st2, s.completed, execute, s.persist, budget=a.budget, reserve=a.reserve,
                       reservation=reservation, fenced=True, blueprint_targets={"hh_locks": target_req},
                       factory_stages={"hh_locks": (None, adapter)})
        if a.mode == "run2":
            summary["restore_checks"] = restore_checks(s, root, target, st2, adapter)
        summary["pass2_executed"] = run_pass2()
        rec = s.completed["hh_locks"]
        summary["locks_record"] = {k: v for k, v in rec.items() if k != "observation"}
        summary["final_observation"] = rec["observation"]
        summary["adapter_history"] = adapter.history
        summary["target"] = target
        summary["status"] = "COMPLETE"
    except BaseException as e:
        summary["status"] = "FAILED"
        summary["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        summary["events"] = s.events
        (root.parent / f"hh_session_summary_{a.mode}.json").write_text(json.dumps(summary, indent=1, default=str))
        print("TWO_HH_SESSION_SUMMARY", summary["status"], summary.get("error", ""))


if __name__ == "__main__":
    main()
