"""v2 volumetric hair adapter for #468 execute_factory_stage (latest contract: finish returns {relative path: SHA-256}).

Native = HairHarpy project. edit/correct author spines + profile modifiers into the native file and run HairHarpy
(modconv every lock, convert the crown, save). measure/reopen loft HairHarpy's lock curves in Blender and return a
contract observation: per lock length / width_mid / thickness_mid (+ global min head clearance), uncertainty,
protected fingerprint (crown + connector + head), operation evidence. Correction = per-key secant on the qualified
gains (len, w, t controls), bounded iterations inside the deadline.
"""
import json
import subprocess
import time
from pathlib import Path

import hh_native as H
import hh_volume as V

HERE = Path(__file__).resolve().parent
MEASURE_ID = "hh_volume_lock_metrics_v2"
OPERATION_ID = "hh_native_spine_profile_controls_v2"
SCOPE_ID = "crown+connector+head"
METRICS = (("length", "len", "u_length"), ("width_mid", "w", "u_section"), ("thickness_mid", "t", "u_section"))


def design_values(bp):
    v = {}
    for lk in bp["locks"]:
        v[f"{lk['id']}_length"] = lk["length"]
        v[f"{lk['id']}_width_mid"] = lk["width"][1]
        v[f"{lk['id']}_thickness_mid"] = lk["thickness"][1]
    v["min_head_clearance"] = bp["targets"]["min_head_clearance"]["value"]
    return v


def tolerances(bp):
    t = {}
    for lk in bp["locks"]:
        for m, _, _ in METRICS:
            t[f"{lk['id']}_{m}"] = bp["targets"][m]["tolerance"]
    t["min_head_clearance"] = bp["targets"]["min_head_clearance"]["tolerance"]
    return t


class VolumeAdapter:
    def __init__(self, bp_path, blender, display, gains, log_dir, head_obj):
        self.bp_path = Path(bp_path)
        self.bp = json.loads(self.bp_path.read_text())
        self.blender, self.display, self.gains = blender, display, gains
        self.head_obj = head_obj
        self.log_dir = Path(log_dir)
        self.history, self.n = [], 0

    def _w(self, native, tag):
        self.n += 1
        w = Path(native).parent / f"w{self.n:02d}_{tag}"
        w.mkdir(exist_ok=True)
        return w

    def _blender(self, args, deadline):
        rem = deadline - time.monotonic()
        if rem <= 5:
            raise TimeoutError("no budget for Blender")
        p = subprocess.run([self.blender, "-b", "--factory-startup", "--python-exit-code", "3", "--python",
                            str(HERE / "hh_volume_blender.py"), "--"] + [str(a) for a in args],
                           capture_output=True, text=True, timeout=min(1800, rem - 2))
        if p.returncode:
            raise RuntimeError("Blender failed: " + p.stdout[-800:] + p.stderr[-300:])

    def apply(self, native, controls, deadline, tag):
        d = H.load(native)
        V.author(d, self.bp, controls)
        d["two_controls"] = controls  # read back by correct(); HairHarpy keeps unknown top-level keys? verified below
        Path(native).write_text(json.dumps(d), encoding="utf-8")
        w = self._w(native, tag)
        log, _ = H.run_app(native, V.events_modconv(d, ["save " + str(native)]), w, deadline, self.display)
        if "saved " + str(native) not in log:
            raise RuntimeError("HairHarpy did not save: " + log[-400:])
        d2 = H.load(native)
        if "two_controls" not in d2:  # HairHarpy dropped it: keep a sidecar next to the native
            (Path(native).parent / "controls.json").write_text(json.dumps(controls, indent=1, sort_keys=True))
        return log

    def controls_of(self, native):
        d = H.load(native)
        if "two_controls" in d:
            return d["two_controls"]
        return json.loads((Path(native).parent / "controls.json").read_text())

    def measure_raw(self, native, deadline, tag):
        out = self._w(native, tag) / "measure.json"
        self._blender(["MEASURE", native, self.bp_path, out], deadline)
        return json.loads(out.read_text()), out

    def observation(self, native, target, m, evidence):
        from shared_blueprint_contract import digest_record
        actual, unc = {}, {}
        for lk in self.bp["locks"]:
            r = m["locks"][lk["id"]]
            for metric, _, ukey in METRICS:
                actual[f"{lk['id']}_{metric}"] = r[metric]
                unc[f"{lk['id']}_{metric}"] = r[ukey]
        actual["min_head_clearance"] = m["global"]["min_head_clearance"]
        unc["min_head_clearance"] = 0.0003
        ctx = {k: target[k] for k in ("target_id", "source_sha256", "coordinate_system", "units", "projection",
                                      "measurement_id", "dependency_fingerprint")}
        return dict(ctx, operation_id=target["operation"]["id"], native_sha256=H.sha(native), evidence_sha256=H.sha(evidence),
                    protected_scope_id=SCOPE_ID, protected_sha256=H.protected_fingerprint(H.load(native)), actual=actual,
                    residuals={k: actual[k] - target["values"][k] for k in actual}, uncertainty=unc,
                    target_contract_sha256=digest_record(target), structure=m["structure"], silhouette=m["silhouette"])

    # ---- #468 adapter interface ----
    def edit(self, native, target, deadline):
        """Design-control plan, then in-session measured correction before handing back to the factory.
        (#468 execute_factory_stage calls correct() only when EVERY failing key is clearly beyond tolerance plus
        uncertainty; a single marginal key would block without correction, so the residual loop runs here too.)"""
        self.history.append({"phase": "edit", "plan": "design controls (len 0, w 1, t 1) - no response model"})
        self.apply(native, V.default_controls(self.bp), deadline, "edit")
        m, ev = self.measure_raw(native, deadline, "edit_m")
        obs = self.observation(native, target, m, ev)
        self.history.append({"phase": "edit_measure", "residuals": obs["residuals"], "structure": m["structure"]})
        self.correct(native, target, obs, deadline)

    def measure(self, native, target, deadline):
        m, ev = self.measure_raw(native, deadline, "measure")
        obs = self.observation(native, target, m, ev)
        self.history.append({"phase": "measure", "residuals": obs["residuals"], "structure": m["structure"]})
        return obs

    def correct(self, native, target, observed, deadline, max_iter=4):
        ctl = self.controls_of(native)
        tol = target["tolerances"]
        gain = json.loads(json.dumps(self.gains))  # {lock: {"len": g, "w": g, "t": g}} measured / control unit
        prev = {}
        obs = observed
        for it in range(max_iter):
            moved = {}
            for lk in self.bp["locks"]:
                for metric, c, _ in METRICS:
                    key = f"{lk['id']}_{metric}"
                    r, u = obs["residuals"][key], obs["uncertainty"][key] + target["uncertainty"][key]
                    if abs(r) <= 0.5 * u or abs(r) + u <= tol[key] * 0.6:
                        continue
                    g = gain[lk["id"]][c]
                    step = -r / g
                    new = ctl[lk["id"]][c] + step
                    if c in ("w", "t"):
                        new = min(2.0, max(0.5, new))
                    prev[(lk["id"], c)] = (ctl[lk["id"]][c], obs["actual"][key])
                    ctl[lk["id"]][c] = new
                    moved[key] = round(new - prev[(lk["id"], c)][0], 6)
            if not moved:
                break
            self.apply(native, ctl, deadline, f"correct{it}")
            m, ev = self.measure_raw(native, deadline, f"correct{it}_m")
            obs = self.observation(native, target, m, ev)
            for (lid, c), (x0, y0) in prev.items():
                key = f"{lid}_{dict((cc, mm) for mm, cc, _ in METRICS)[c]}"
                x1, y1 = ctl[lid][c], obs["actual"][key]
                if abs(x1 - x0) > 1e-9:
                    g = (y1 - y0) / (x1 - x0)
                    if g * gain[lid][c] > 0 and 0.2 < abs(g / gain[lid][c]) < 5:  # same sign, sane: secant update
                        gain[lid][c] = g
            prev = {}
            self.history.append({"phase": f"correct{it}", "moved": moved, "residuals": obs["residuals"],
                                 "structure": m["structure"]})
        return obs

    def finish(self, native, target, deadline):
        root = Path(native).parent
        crown = root / "crown.obj"
        H.run_app(native, f"room hair;wait 300;exportf obj {crown}", self._w(native, "crown"), deadline, self.display)
        out = root / "finish.json"
        self._blender(["FINISH", native, self.bp_path, out, root / "hair_v2_530.blend", root / "renders", self.head_obj, crown],
                      deadline)
        f = json.loads(out.read_text())
        self.history.append({"phase": "finish", "uv_ok": f["uv_ok"]})
        if not f["uv_ok"]:
            raise RuntimeError("strand UV QA failed")
        (root / "adapter_history.json").write_text(json.dumps(self.history, indent=1, default=str))
        files = [out, root / "hair_v2_530.blend", crown, root / "adapter_history.json"] + sorted((root / "renders").rglob("*.png"))
        if (root / "controls.json").exists():
            files.append(root / "controls.json")
        return {p.relative_to(root).as_posix(): H.sha(p) for p in files}

    def reopen(self, native, target, deadline):
        before = H.sha(native)
        H.run_app(native, "room hair;wait 300;tree;meshdump", self._w(native, "reopen_hh"), deadline, self.display)
        if H.sha(native) != before:
            raise RuntimeError("reopen modified the native project")
        m, ev = self.measure_raw(native, deadline, "reopen")
        obs = self.observation(native, target, m, ev)
        obs["reopen_process"] = "fresh HairHarpy process (project open) + fresh Blender process (loft + measure)"
        self.history.append({"phase": "reopen", "actual": obs["actual"]})
        return obs
