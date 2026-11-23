"""v3 hair adapter (#468 8c1d5ae factory): v2 loft/HairHarpy path + design registry targets and layered placement.

Targets per lock: length, width_mid, thickness_mid, kappa_50, taper_085 (corrected) and width_root, thickness_root
(checked); global: min_head_clearance, max_penetration_depth (vertex inside another closed lock deeper than 1 mm,
outside the root zone). Controls: len, w, t, bend, tipw (per lock, qualified gains) and layer (radial offset,
pairwise penetration correction with a qualified gain). Widths are never reduced to clear a penetration.
"""
import json

import hh_native as H
from hh_volume_adapter import SCOPE_ID, VolumeAdapter

MEASURE_ID = "hh_volume_lock_metrics_v3"
OPERATION_ID = "hh_native_spine_profile_layer_controls_v3"
CORRECTED = (("length", "len", "u_length"), ("width_mid", "w", "u_section"), ("thickness_mid", "t", "u_section"),
             ("kappa_50", "bend", "u_kappa"), ("taper_085", "tipw", "u_taper"))
PHASES = (("separation", ()), ("shape", ("len", "w", "t", "tipw")), ("separation_b", ()), ("curvature", ("bend",)),
          ("shape_recheck", ("len",)), ("curvature_recheck", ("bend",)), ("separation_c", ()))
RANK = {"top": 0, "back": 1, "side": 1, "face_frame": 2, "bang": 3}
DAMP = {"len": 0.9, "w": 0.9, "t": 0.9, "tipw": 0.8, "bend": 0.5}
CHECKED = (("width_root", "u_section"), ("thickness_root", "u_section"))
LAYER_MAX = 0.018  # about one lock thickness
TOP_LAYER_MAX = 0.006  # top cover tiles stay under the hanging locks (one top-lock thickness)


def lock_depth(obs):
    d = {}
    for p in obs.get("penetration_pairs", []):
        for x in (p["a"], p["b"]):
            d[x] = max(d.get(x, 0.0), p["max_depth"])
    return d


def design_values(bp):
    v = {}
    for lk in bp["locks"]:
        g = lk["registry"]
        v[f"{lk['id']}_length"] = lk["length"]
        for m in ("width_mid", "thickness_mid", "kappa_50", "taper_085", "width_root", "thickness_root"):
            v[f"{lk['id']}_{m}"] = g[m]
    v["min_head_clearance"] = bp["targets"]["min_head_clearance"]["value"]
    v["max_penetration_depth"] = 0.0
    return v


def tolerances(bp):
    t, T = {}, bp["targets"]
    for lk in bp["locks"]:
        for m in ("length", "width_mid", "thickness_mid", "taper_085", "width_root", "thickness_root"):
            t[f"{lk['id']}_{m}"] = T[m]["tolerance"]
        t[f"{lk['id']}_kappa_50"] = T["kappa_50"]["tolerance_abs"] + T["kappa_50"]["tolerance_rel"] * lk["registry"]["kappa_50"]
    t["min_head_clearance"] = T["min_head_clearance"]["tolerance"]
    t["max_penetration_depth"] = T["max_penetration_depth"]["tolerance"]
    return t


class V3Adapter(VolumeAdapter):
    def observation(self, native, target, m, evidence):
        from shared_blueprint_contract import digest_record
        actual, unc = {}, {}
        for lk in self.bp["locks"]:
            r = m["locks"][lk["id"]]
            for metric, _, uk in CORRECTED:
                actual[f"{lk['id']}_{metric}"], unc[f"{lk['id']}_{metric}"] = r[metric], r[uk]
            for metric, uk in CHECKED:
                actual[f"{lk['id']}_{metric}"], unc[f"{lk['id']}_{metric}"] = r[metric], r[uk]
        actual["min_head_clearance"], unc["min_head_clearance"] = m["global"]["min_head_clearance"], 0.0003
        actual["max_penetration_depth"], unc["max_penetration_depth"] = m["global"]["max_penetration_depth"], 0.0002
        ctx = {k: target[k] for k in ("target_id", "source_sha256", "coordinate_system", "units", "projection",
                                      "measurement_id", "dependency_fingerprint")}
        return dict(ctx, operation_id=target["operation"]["id"], native_sha256=H.sha(native), evidence_sha256=H.sha(evidence),
                    protected_scope_id=SCOPE_ID, protected_sha256=H.protected_fingerprint(H.load(native)), actual=actual,
                    residuals={k: actual[k] - target["values"][k] for k in actual}, uncertainty=unc,
                    target_contract_sha256=digest_record(target), structure=m["structure"],
                    penetration={k: v for k, v in m["penetration"].items() if k != "pairs"},
                    penetration_pairs=[p for p in m["penetration"]["pairs"] if p["class"] == "penetration"],
                    silhouette=m["silhouette"])

    def correct(self, native, target, observed, deadline, max_iter=3):
        """Phased in-session correction (run 2026-11-23 diverged when every control moved at once): penetration
        separation first, then length/width/thickness/taper, then damped curvature, then a length re-check. Each
        iteration re-measures; secant gains are refined only from informative, same-sign steps."""
        ctl = self.controls_of(native)
        tol = target["tolerances"]
        gain = json.loads(json.dumps(self.gains))
        order = [lk["id"] for lk in self.bp["locks"]]
        role = {lk["id"]: lk["role"] for lk in self.bp["locks"]}
        shell = {lk["id"]: 1 if lk.get("shell") == "outer" else 0 for lk in self.bp["locks"]}
        obs = observed
        before, frozen, halved = observed, set(), set()
        self.frozen = frozen
        for phase, controls in PHASES:
            for it in range(max_iter + 2 if phase.startswith("separation") else max_iter):
                moved, prev = {}, {}
                if phase.startswith("separation"):
                    seen = set()
                    for p in obs.get("penetration_pairs", []):
                        a, b = p["a"], p["b"]
                        if (b, a) in seen:
                            continue
                        seen.add((a, b))
                        key_of = lambda x: (RANK[role[x]], shell[x], ctl[x]["layer"], order.index(x))
                        outer = a if key_of(a) >= key_of(b) else b  # design hierarchy: top < hanging < bang, then inner < outer shell
                        inner = b if outer == a else a
                        step = p["max_depth"] + 0.0008
                        cap = TOP_LAYER_MAX if role[outer] == "top" else LAYER_MAX
                        new = min(cap, ctl[outer]["layer"] + step)
                        if new > ctl[outer]["layer"] + 1e-6:
                            moved[f"{outer}_layer"] = round(new - ctl[outer]["layer"], 6)
                            ctl[outer]["layer"] = new
                        elif ctl[inner]["layer"] > 1e-6:  # outer at the volume cap: bring the inner lock back down
                            low = max(0.0, ctl[inner]["layer"] - step)
                            moved[f"{inner}_layer"] = round(low - ctl[inner]["layer"], 6)
                            ctl[inner]["layer"] = low
                else:
                    for lk in self.bp["locks"]:
                        for metric, c, _ in CORRECTED:
                            if c not in controls:
                                continue
                            key = f"{lk['id']}_{metric}"
                            r, u = obs["residuals"][key], obs["uncertainty"][key] + target["uncertainty"][key]
                            if abs(r) <= 0.5 * u or abs(r) + u <= tol[key] * 0.6:
                                continue
                            g = gain[lk["id"]][c]
                            if not g or (lk["id"], c) in frozen:  # not qualified / guarded: checked only
                                continue
                            new = ctl[lk["id"]][c] - DAMP[c] * r / g
                            lim = {"w": (0.6, 1.8), "t": (0.6, 1.8), "tipw": (0.3, 4.0), "bend": (0.0, 0.05)}.get(c)
                            if lim:
                                new = min(lim[1], max(lim[0], new))
                            if abs(new - ctl[lk["id"]][c]) < 1e-9:
                                continue
                            prev[(lk["id"], c, key)] = (ctl[lk["id"]][c], obs["actual"][key])
                            moved[key] = round(new - ctl[lk["id"]][c], 6)
                            ctl[lk["id"]][c] = new
                if not moved:
                    break
                self.apply(native, ctl, deadline, f"{phase}{it}")
                m, ev = self.measure_raw(native, deadline, f"{phase}{it}_m")
                obs = self.observation(native, target, m, ev)
                for (lid, c, key), (x0, y0) in prev.items():
                    x1, y1 = ctl[lid][c], obs["actual"][key]
                    if abs(x1 - x0) > 1e-9 and gain[lid][c]:
                        g = (y1 - y0) / (x1 - x0)
                        if g * gain[lid][c] > 0 and 0.2 < abs(g / gain[lid][c]) < 5:
                            gain[lid][c] = g
                # protected-scope guard: a shape/curvature step may not push a lock into a neighbour nor break another
                # in-tolerance metric of the same lock (coupling). First trip keeps half the step (Causal Retry: smaller
                # step, same qualified op) and is re-verified; a second trip restores the last safe value and freezes.
                self.history.append({"phase": f"{phase}{it}", "moved": moved, "residuals": obs["residuals"],
                                     "penetration": obs["penetration"], "structure": obs["structure"]})
                if not phase.startswith("separation"):
                    def ok(o, k):
                        return abs(o["residuals"][k]) + o["uncertainty"][k] + target["uncertainty"][k] <= tol[k]
                    check = dict(prev)
                    for rnd in range(2):
                        # pairs the separation phases can resolve (different design rank or shell) are left to them
                        same = lambda p: RANK[role[p["a"]]] == RANK[role[p["b"]]] and shell[p["a"]] == shell[p["b"]]
                        d0 = lock_depth({"penetration_pairs": [p for p in before.get("penetration_pairs", []) if same(p)]})
                        d1 = lock_depth({"penetration_pairs": [p for p in obs.get("penetration_pairs", []) if same(p)]})
                        guard, nxt = [], {}
                        for (lid, c, key), (x0, y0) in check.items():
                            pushed = d1.get(lid, 0.0) > max(d0.get(lid, 0.0) + 0.0003, 0.001)
                            broke = [f"{lid}_{m2}" for m2, c2, _ in CORRECTED if c2 != c
                                     and ok(before, f"{lid}_{m2}") and not ok(obs, f"{lid}_{m2}")]
                            if not (pushed or broke):
                                continue
                            if rnd == 0 and (lid, c) not in halved:
                                ctl[lid][c] = x0 + 0.5 * (ctl[lid][c] - x0)
                                halved.add((lid, c))
                                nxt[(lid, c, key)] = (x0, y0)
                                action = "half_step"
                            else:
                                ctl[lid][c] = x0
                                frozen.add((lid, c))
                                action = "frozen"
                            guard.append({"control": f"{lid}:{c}", "pushed_into_neighbour": pushed, "broke": broke,
                                          "action": action})
                        if not guard:
                            break
                        self.apply(native, ctl, deadline, f"{phase}{it}g{rnd}")
                        m, ev = self.measure_raw(native, deadline, f"{phase}{it}g{rnd}_m")
                        obs = self.observation(native, target, m, ev)
                        self.history.append({"phase": f"{phase}{it}_guard{rnd}", "guard": guard, "residuals": obs["residuals"],
                                             "penetration": obs["penetration"], "structure": obs["structure"]})
                        check = nxt
                before = obs
        return obs
