"""HairHarpy lock adapter for the #468 shared factory stage (execute_factory_stage).

Native = HairHarpy project (.hairmesh). Every phase is a real HairHarpy and/or Blender 5.3.0 process bounded by the
controller deadline. The adapter supplies edit / measure / correct / finish / reopen; #468 owns planning, lease,
fencing, quarantine and checkpoint acceptance (shared_blueprint_contract.measurement_issues).
"""
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

import hh_native as H

HERE = Path(__file__).resolve().parent
MEASURE_ID = "hh_lock_surface_length_v1"
OPERATION_ID = "hh_native_tip_anchor_move"
SCOPE_ID = "crown+connector+head"


def target_keys(bp):
    return [f"{lk['id']}_length" for lk in bp["locks"]] + ["asymmetry_left_over_right", "min_head_clearance"]


def design_values(bp):
    v = {f"{lk['id']}_length": lk["length"] for lk in bp["locks"]}
    left = [lk["length"] for lk in bp["locks"] if lk["side"] == "left"]
    right = [lk["length"] for lk in bp["locks"] if lk["side"] == "right"]
    v["asymmetry_left_over_right"] = (sum(left) / len(left)) / (sum(right) / len(right))
    v["min_head_clearance"] = bp["targets"]["min_head_clearance"]["value"]
    return v


class HairHarpyLockAdapter:
    def __init__(self, bp_path, blender, display, response, log_dir):
        self.bp_path = Path(bp_path)
        self.bp = json.loads(self.bp_path.read_text())
        self.blender, self.display = blender, display
        self.response = response  # {"slope": {lock: dL/dtip_y}, "evidence_sha256": ...}
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.history = []
        self.n = 0

    # ---------- helpers ----------
    def _work(self, native, tag):
        self.n += 1
        w = Path(native).parent / f"w{self.n:02d}_{tag}"
        w.mkdir(exist_ok=True)
        return w

    def _blender(self, args, deadline):
        rem = deadline - time.monotonic()
        if rem <= 5:
            raise TimeoutError("no budget for Blender measurement")
        p = subprocess.run([self.blender, "-b", "--factory-startup", "--python-exit-code", "3", "--python",
                            str(HERE / "hh_measure_blender.py"), "--"] + args,
                           capture_output=True, text=True, timeout=min(600, rem - 2))
        if p.returncode:
            raise RuntimeError("Blender measurement failed: " + p.stdout[-600:] + p.stderr[-300:])

    def _rebuild(self, native, controls, deadline, tag):
        d = H.load(native)
        H.author_locks(d, self.bp, controls)
        Path(native).write_text(json.dumps(d), encoding="utf-8")
        w = self._work(native, tag)
        log, _ = H.run_app(native, H.cocoon_convert_events(d, ["save " + str(native)]), w, deadline, self.display)
        if f"convsum: {len(self.bp['locks'])} locks" not in log or "saved " + str(native) not in log:
            raise RuntimeError("HairHarpy did not convert all locks / save: " + log[-500:])
        H.load(native)  # reopenable project (app key present)
        return log

    def _export_measure(self, native, deadline, tag):
        w = self._work(native, tag)
        obj = w / "locks.obj"
        log, shot = H.run_app(native, f"room hair;wait 400;tree;exportf obj {obj}", w, deadline, self.display)
        if not obj.exists():
            raise RuntimeError("HairHarpy export missing: " + log[-300:])
        out = w / "measure.json"
        self._blender(["MEASURE", str(obj), str(self.bp_path), str(out)], deadline)
        return json.loads(out.read_text()), out, log

    def observation(self, native, target, m, evidence):
        d = H.load(native)
        actual, unc = {}, {}
        for lk in self.bp["locks"]:
            k = f"{lk['id']}_length"
            actual[k] = m["locks"][lk["id"]]["length"]
            unc[k] = m["locks"][lk["id"]]["length_uncertainty"]
        actual["asymmetry_left_over_right"] = m["global"]["asymmetry_left_over_right"]
        lu = [m["locks"][lk["id"]]["length_uncertainty"] / m["locks"][lk["id"]]["length"] for lk in self.bp["locks"]]
        unc["asymmetry_left_over_right"] = actual["asymmetry_left_over_right"] * math.sqrt(sum(x * x for x in lu) / len(lu))
        actual["min_head_clearance"] = m["global"]["min_head_clearance"]
        unc["min_head_clearance"] = 0.0005
        ctx = {k: target[k] for k in ("target_id", "source_sha256", "coordinate_system", "units", "projection",
                                      "measurement_id", "dependency_fingerprint")}
        from shared_blueprint_contract import digest_record
        return dict(ctx, operation_id=target["operation"]["id"], native_sha256=H.sha(native),
                    evidence_sha256=H.sha(evidence), protected_scope_id=SCOPE_ID,
                    protected_sha256=H.protected_fingerprint(d), actual=actual,
                    residuals={k: actual[k] - target["values"][k] for k in actual}, uncertainty=unc,
                    target_contract_sha256=digest_record(target), technical=m["technical"], silhouette=m["silhouette"])

    def initial_controls(self, native):
        d = H.load(native)
        roots = H.connector_roots(d)
        ctl = {}
        for lk in self.bp["locks"]:
            ry = (roots[lk["roots"][0]][1][1] + roots[lk["roots"][1]][1][1]) / 2
            s = self.response["slope"].get(lk["id"], -1.0)
            # design length -> tip height through the qualified response model (intercept from its reference point)
            ref = self.response["reference"][lk["id"]]
            ctl[lk["id"]] = {"tip_y": ref["tip_y"] + (lk["length"] - ref["length"]) / s, "bend": lk["bend"]}
        return ctl

    # ---------- #468 adapter interface ----------
    def plan_controls(self, native):
        """Design-to-control plan WITHOUT the response model (tip height = root height - 0.90 x design length).
        The correction stage then uses the qualified response model."""
        d = H.load(native)
        roots = H.connector_roots(d)
        return {lk["id"]: {"tip_y": (roots[lk["roots"][0]][1][1] + roots[lk["roots"][1]][1][1]) / 2 - 0.90 * lk["length"],
                           "bend": lk["bend"]} for lk in self.bp["locks"]}

    def edit(self, native, target, deadline):
        self.history.append({"phase": "edit", "t": time.time(), "plan": "naive 0.90 x length"})
        self._rebuild(native, self.plan_controls(native), deadline, "edit")

    def measure(self, native, target, deadline):
        m, ev, _ = self._export_measure(native, deadline, "measure")
        obs = self.observation(native, target, m, ev)
        self.history.append({"phase": "measure", "actual": obs["actual"], "residuals": obs["residuals"]})
        return obs

    def correct(self, native, target, observed, deadline, max_iter=4):
        """In-session correction: per-lock secant update of the tip anchor from measured residuals."""
        tol = target["tolerances"]
        d = H.load(native)
        ctl = {k: dict(v, bend=next(l["bend"] for l in self.bp["locks"] if l["id"] == k)) for k, v in H.lock_controls(d).items()}
        slope = dict(self.response["slope"])
        prev = {k: (ctl[k]["tip_y"], observed["actual"][f"{k}_length"]) for k in ctl}
        obs = observed
        for it in range(max_iter):
            moved = {}
            for k in ctl:
                key = f"{k}_length"
                r = obs["residuals"][key]
                u = obs["uncertainty"][key] + target["uncertainty"][key]
                if abs(r) <= 0.5 * u or abs(r) + u <= tol[key] * 0.6:  # inside the measurable band: stop
                    continue
                ctl[k]["tip_y"] -= r / slope[k]
                moved[k] = round(-r / slope[k], 6)
            if not moved:
                break
            self._rebuild(native, ctl, deadline, f"correct{it}")
            m, ev, _ = self._export_measure(native, deadline, f"correct{it}_measure")
            obs = self.observation(native, target, m, ev)
            for k in moved:  # refine the response (secant) where the step was informative
                y0, l0 = prev[k]
                y1, l1 = ctl[k]["tip_y"], obs["actual"][f"{k}_length"]
                if abs(y1 - y0) > 1e-4 and (l1 - l0) / (y1 - y0) < -0.2:
                    slope[k] = (l1 - l0) / (y1 - y0)
                prev[k] = (y1, l1)
            self.history.append({"phase": f"correct{it}", "moved_tip_y": moved, "residuals": obs["residuals"],
                                 "slope": {k: round(v, 4) for k, v in slope.items()}})
        return obs

    def finish(self, native, target, deadline):
        """HairHarpy Topology-room UV unfold/pack, then Blender UV transfer/QA + PBR factory + preview + native .blend."""
        w = self._work(native, "finish")
        obj = Path(native).parent / "locks.obj"
        H.run_app(native, f"room hair;wait 300;exportf obj {obj}", w / "a", deadline, self.display)
        uv_obj = Path(native).parent / "locks_uv_merged.obj"
        ev = ["newproj", "room topo", f"import {obj}", "wait 500", "select 3", "uv open", "wait 200", "uv angle 50",
              "uv unfoldall", "uv packall", "uv checks", "uv stat", f"exportf obj {uv_obj}"]
        log, _ = H.run_app(None, ";".join(ev), w / "b", deadline, self.display)
        (Path(native).parent / "hh_uv_session.log").write_text(log)
        if "flipped 0 overlap 0" not in log:
            raise RuntimeError("HairHarpy UV checks not clean: " + log[-400:])
        out = Path(native).parent / "finish.json"
        self._blender(["FINISH", str(obj), str(uv_obj), str(self.bp_path), str(out),
                       str(Path(native).parent / "hair_qual_530.blend"), str(Path(native).parent / "renders")], deadline)
        f = json.loads(out.read_text())
        self.history.append({"phase": "finish", "uv_ok": f["uv_ok"], "uv": f["uv"]})
        if not f["uv_ok"]:
            raise RuntimeError("UV QA failed")

    def reopen(self, native, target, deadline):
        before = H.sha(native)
        m, ev, log = self._export_measure(native, deadline, "reopen")
        if H.sha(native) != before:
            raise RuntimeError("reopen modified the native project")
        obs = self.observation(native, target, m, ev)
        obs["reopen_process"] = "fresh HairHarpy process + fresh Blender process"
        self.history.append({"phase": "reopen", "actual": obs["actual"]})
        (Path(native).parent / "adapter_history.json").write_text(json.dumps(self.history, indent=1, default=str))
        return obs
