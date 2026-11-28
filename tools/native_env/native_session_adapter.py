#!/usr/bin/env python3
"""Long-session native Blender adapter bound to the #468 shared planner (pinned, hash-verified).

Uses #468 session_plan.ready() for checkpoint validity / dependency invalidation and
bounded_operation.run_operation() for deadline-enforced subprocesses. It does NOT acquire the
production shared lease (SYNC_UNVERIFIED; owner #468) and only edits a CALIBRATION fixture.

run1: legacy 5.2.4 -> 5.3.0 coexistence, s1..s5 with mid-stage interruption + quarantine + resume,
      then stops (session budget) leaving s6 for another run.
run2: restore run1 artifact, negative controls (tamper / stale fingerprint / missing file),
      independent reopen of restored checkpoint, then execute remaining s6 only.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_COMMIT = "5c067e518d4d764dc1499920fe4a2513340c96b9"  # PR #468 HEAD
ENGINE_FILES = {
    "session_plan.py": "113212d89784d97ea5b9800951bd1a58bf0afbeedf680f453463a2b9223baaa6",
    "bounded_operation.py": "851c2854d94b0433d82354c30c23d156d31382eb23a0c1fcd4e8f6bb21c7ebe2",
}
CODE = ("native_stages.py", "pbr_factory.py", "render_views.py")
STAGES = [  # id, deps, budget seconds
    ("s1_build", [], 180), ("s2_calibrate", ["s1_build"], 300), ("s3_correct_shape", ["s2_calibrate"], 300),
    ("s4_material", ["s3_correct_shape"], 900), ("s5_render_preview", ["s4_material"], 900),
    ("s6_render_hq", ["s5_render_preview"], 5400)]
GEOM_KEYS = ("eye_spacing_over_head_height", "front_hair_hem_span_over_head_height", "head_height",
             "topology_CAL-head", "topology_CAL-hair_shell", "controls")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_engine(d):
    mods = {}
    for name, digest in ENGINE_FILES.items():
        p = Path(d) / name
        if sha(p) != digest:
            raise SystemExit("ENGINE_HASH_MISMATCH:" + name)
        spec = importlib.util.spec_from_file_location(name[:-3], p)
        mods[name[:-3]] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mods[name[:-3]])
    return mods["session_plan"], mods["bounded_operation"]


class Session:
    def __init__(self, a, plan, bop):
        self.a, self.plan, self.bop = a, plan, bop
        self.work = Path(a.work).resolve()
        self.root = self.work / "ckpt"
        self.quar = self.work / "quarantine"
        for d in (self.root, self.quar):
            d.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.root / "ledger.json"
        self.completed = json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {}
        self.events = []
        self.version = self.blender_version(a.blender)
        self.stages = self.build_stages()

    def log(self, kind, **kw):
        kw.update(event=kind, t=round(time.time(), 3))
        self.events.append(kw)
        print("TWO_EVENT", json.dumps(kw, sort_keys=True), flush=True)

    @staticmethod
    def blender_version(b):
        out = subprocess.run([b, "-b", "--factory-startup", "--python-expr",
                              "import bpy;print('VER', bpy.app.version_string, bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash)"],
                             capture_output=True, text=True, timeout=120, check=True).stdout
        return [l for l in out.splitlines() if l.startswith("VER ")][0][4:]

    def build_stages(self):
        code = {n: sha(HERE / n) for n in CODE}
        bp = sha(self.a.blueprint)
        fps, out = {}, []
        for sid, deps, secs in STAGES:
            comp = {"stage": sid, "code": code, "blender": self.version, "deps": [fps[d] for d in deps],
                    "blueprint": bp if sid in ("s3_correct_shape", "s4_material") else None}
            fps[sid] = hashlib.sha256(json.dumps(comp, sort_keys=True).encode()).hexdigest()
            out.append({"id": sid, "deps": deps, "seconds": secs, "qualified": True, "fingerprint": fps[sid]})
        return out

    def blender(self, args, deadline, env=None):
        argv = [self.a.blender, "-b"] + args
        log = open(self.work / "blender.log", "a")
        try:
            # run_operation inherits stdio; redirect at fd level for evidence
            old = os.dup(1), os.dup(2)
            os.dup2(log.fileno(), 1)
            os.dup2(log.fileno(), 2)
            try:
                return self.bop.run_operation(argv, deadline, env=env, grace=5)
            finally:
                os.dup2(old[0], 1)
                os.dup2(old[1], 2)
        finally:
            log.close()

    def measure(self, blend, deadline, blender=None):
        rep = self.work / ("measure_" + Path(blend).stem + ".json")
        b = blender or self.a.blender
        subprocess.run([b, "-b", str(blend), "--factory-startup", "--python-exit-code", "3", "--python",
                        str(HERE / "native_stages.py"), "--", "measure", "--report", str(rep)],
                       check=True, timeout=max(5, deadline - time.monotonic()), capture_output=True)
        return json.loads(rep.read_text())

    def execute(self, stage, deadline, hold=None):
        sid = stage["id"]
        partial = self.root / (sid + ".partial.blend")
        report = self.root / (sid + ".report.json")
        args = []
        if stage["deps"]:
            args.append(str(self.root / self.completed[stage["deps"][0]]["path"]))
        args += ["--factory-startup", "--python-exit-code", "3", "--python", str(HERE / "native_stages.py"), "--", sid,
                 "--out", str(partial), "--report", str(report), "--blueprint", str(Path(self.a.blueprint).resolve()),
                 "--outdir", str(self.root / "renders")]
        env = dict(os.environ)
        if hold:
            env["TWO_TEST_HOLD_SECONDS"] = str(hold)
        t0 = time.monotonic()
        try:
            self.blender(args, deadline, env=env)
        except BaseException as e:
            for p in (partial, report):
                if p.exists():
                    shutil.move(str(p), self.quar / (p.name + ".%d" % int(time.time())))
            self.log("stage_failed", stage=sid, error=type(e).__name__, detail=str(e)[:200], quarantined=True)
            raise
        rep = json.loads(report.read_text())
        final = self.root / (sid + ".blend")
        os.replace(partial, final)  # promote only after a complete save
        digest = sha(final)
        if digest != rep["output_sha256"]:
            raise RuntimeError("OUTPUT_HASH_CHANGED_AFTER_SAVE")
        re = self.measure(final, deadline)  # independent process reopen
        same = {k: re["metrics"].get(k) == rep["metrics"].get(k) for k in rep["metrics"]}
        if not all(same.values()) or re.get("last_stage_in_file") != sid:
            raise RuntimeError("REOPEN_MISMATCH:%s" % same)
        rep_path = report.rename(self.root / (sid + ".report.json"))
        self.log("stage_done", stage=sid, seconds=round(time.monotonic() - t0, 2), sha256=digest)
        return {"path": final.name, "sha256": digest, "reopened": True, "fingerprint": stage["fingerprint"],
                "report": rep_path.name, "report_sha256": sha(rep_path), "metrics": rep["metrics"]}

    def persist(self):
        tmp = self.ledger_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self.completed, f, indent=1, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.ledger_path)
        lines = []
        for p in sorted(self.root.rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS":
                lines.append("%s  %s" % (sha(p), p.relative_to(self.root).as_posix()))
        (self.root / "SHA256SUMS").write_text("\n".join(lines) + "\n")

    def ready(self, completed=None, root=None, stages=None):
        remaining = self.deadline - time.monotonic()
        return self.plan.ready(stages or self.stages, self.completed if completed is None else completed,
                               root or self.root, remaining, self.a.reserve)

    def loop(self, stop_after=None):
        executed = []
        while True:
            avail = self.ready()
            if not avail:
                break
            stage = next(s for s in self.stages if s["id"] == avail[0])
            deadline = min(self.deadline - self.a.reserve, time.monotonic() + stage["seconds"])
            result = self.execute(stage, deadline)
            invalid = {stage["id"]}
            while True:  # dependency invalidation (same rule as #468 controller)
                grown = invalid | {s["id"] for s in self.stages if set(s["deps"]) & invalid}
                if grown == invalid:
                    break
                invalid = grown
            self.completed = {k: v for k, v in self.completed.items() if k not in invalid}
            self.completed[stage["id"]] = result
            self.persist()
            executed.append(stage["id"])
            if stage["id"] == stop_after:
                self.log("session_budget_stop", after=stop_after, remaining=self.ready())
                break
        return executed


def legacy_coexistence(s, b524):
    """5.2.4 creates a legacy fixture; 5.3.0 opens a COPY; 5.2.4 original bytes must stay unchanged."""
    d = s.work / "legacy524"
    d.mkdir(exist_ok=True)
    src = d / "legacy_524.blend"
    subprocess.run([b524, "-b", "--factory-startup", "--python-exit-code", "3", "--python", str(HERE / "native_stages.py"),
                    "--", "s1_build", "--out", str(src), "--report", str(d / "legacy_524_build.json")],
                   check=True, timeout=300, capture_output=True)
    before = sha(src)
    m524 = s.measure(src, time.monotonic() + 300, blender=b524)
    copy = d / "legacy_524_copy_for_530.blend"
    shutil.copy2(src, copy)
    m530 = s.measure(copy, time.monotonic() + 300)
    diff = {k: (m524["metrics"].get(k), m530["metrics"].get(k)) for k in GEOM_KEYS if m524["metrics"].get(k) != m530["metrics"].get(k)}
    res = {"blender_524": m524["blender"], "blender_530": m530["blender"], "legacy_sha256": before,
           "legacy_unchanged": sha(src) == before, "metric_differences": diff,
           "result": "PASS" if sha(src) == before and not diff and m524["blender"].startswith("5.2.4") and m530["blender"].startswith("5.3.0") else "FAIL"}
    s.log("legacy_coexistence", **res)
    return res


def run1(s, a):
    out = {}
    if a.blender524:
        out["legacy_coexistence"] = legacy_coexistence(s, a.blender524)
    s.loop(stop_after="s1_build")
    # interruption: s2 is killed mid-stage by the bounded deadline; previous checkpoint must survive
    st = next(x for x in s.stages if x["id"] == "s2_calibrate")
    before = dict(s.completed)
    before_sha = sha(s.root / s.completed["s1_build"]["path"])
    try:
        s.execute(st, time.monotonic() + 25, hold=120)
        out["interruption"] = {"result": "FAIL", "reason": "stage was not interrupted"}
    except (TimeoutError, subprocess.TimeoutExpired):
        ok = (s.completed == before and sha(s.root / s.completed["s1_build"]["path"]) == before_sha
              and not (s.root / "s2_calibrate.blend").exists() and not (s.root / "s2_calibrate.partial.blend").exists()
              and s.ready() == ["s2_calibrate"])
        out["interruption"] = {"result": "PASS" if ok else "FAIL", "killed_stage": "s2_calibrate",
                               "previous_checkpoint_sha256": before_sha, "resume_plan": s.ready(),
                               "quarantined_files": sorted(p.name for p in s.quar.iterdir())}
    s.log("interruption_test", **out["interruption"])
    out["executed"] = s.loop(stop_after="s5_render_preview")
    out["remaining_after_session"] = s.ready()
    return out


def run2(s, a):
    src = Path(a.restore).resolve()
    shutil.copytree(src / "ckpt", s.root, dirs_exist_ok=True)
    s.completed = json.loads(s.ledger_path.read_text())
    out = {"restored_from": str(src), "restored_ledger_sha256": sha(s.ledger_path)}
    avail = s.ready()
    out["plan_after_restore"] = avail
    neg = {}
    scratch = s.work / "negative"
    for case in ("tamper_s4", "stale_s3", "missing_s5"):
        r = scratch / case
        shutil.copytree(s.root, r)
        comp = json.loads((r / "ledger.json").read_text())
        stages = [dict(x) for x in s.stages]
        if case == "tamper_s4":
            p = r / comp["s4_material"]["path"]
            b = bytearray(p.read_bytes())
            b[len(b) // 2] ^= 0xFF
            p.write_bytes(bytes(b))
            expect = ["s4_material"]
        elif case == "stale_s3":
            next(x for x in stages if x["id"] == "s3_correct_shape")["fingerprint"] = "0" * 64
            expect = ["s3_correct_shape"]
        else:
            (r / comp["s5_render_preview"]["path"]).unlink()
            expect = ["s5_render_preview"]
        got = s.ready(completed=comp, root=r, stages=stages)
        neg[case] = {"expected_next": expect, "planner_next": got, "result": "PASS" if got == expect else "FAIL"}
    out["negative_controls"] = neg
    s.log("negative_controls", **neg)
    last = s.completed["s5_render_preview"]
    re = s.measure(s.root / last["path"], time.monotonic() + 300)
    same = all(re["metrics"].get(k) == last["metrics"].get(k) for k in last["metrics"])
    out["cross_run_reopen"] = {"checkpoint": last["path"], "sha256": sha(s.root / last["path"]),
                               "ledger_sha256": last["sha256"], "metrics_equal": same,
                               "blender": re["blender"], "result": "PASS" if same and sha(s.root / last["path"]) == last["sha256"] else "FAIL"}
    s.log("cross_run_reopen", **out["cross_run_reopen"])
    out["executed"] = s.loop()
    out["remaining_after_session"] = s.ready()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blender", required=True)
    ap.add_argument("--blender524")
    ap.add_argument("--engine", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--blueprint", required=True)
    ap.add_argument("--mode", choices=("run1", "run2"), required=True)
    ap.add_argument("--restore")
    ap.add_argument("--budget", type=float, default=19800)
    ap.add_argument("--reserve", type=float, default=900)
    a = ap.parse_args()
    plan, bop = load_engine(a.engine)
    s = Session(a, plan, bop)
    s.deadline = time.monotonic() + a.budget
    summary = {"mode": a.mode, "engine_commit": ENGINE_COMMIT, "engine_files": ENGINE_FILES, "blender": s.version,
               "blueprint_sha256": sha(a.blueprint), "stage_fingerprints": {x["id"]: x["fingerprint"] for x in s.stages},
               "lease": "NOT_ACQUIRED (production shared lease SYNC_UNVERIFIED; owner #468)", "fixture": "CALIBRATION_ONLY"}
    try:
        summary.update(run1(s, a) if a.mode == "run1" else run2(s, a))
        summary["status"] = "COMPLETE"
    except Exception as e:  # noqa: BLE001
        summary["status"] = "FAILED"
        summary["error"] = "%s: %s" % (type(e).__name__, e)
        raise
    finally:
        summary["events"] = s.events
        summary["ledger"] = s.completed
        (s.work / ("summary_%s.json" % a.mode)).write_text(json.dumps(summary, indent=1, sort_keys=True))
        print("TWO_SUMMARY", summary["status"], json.dumps({k: v for k, v in summary.items() if k not in ("events", "ledger")})[:3000])


if __name__ == "__main__":
    main()
