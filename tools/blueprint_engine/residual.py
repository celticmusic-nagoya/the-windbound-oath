"""Residual Engine.

Two-sided: |r|+u<=t PASS, |r|-u>t OUTSIDE, otherwise HOLD (#468 metric_state).
Lower bound (target["lower_bound"]): r = x - L; r-u>=0 PASS, r+u<0 OUTSIDE,
otherwise HOLD. u = target uncertainty + observation uncertainty, as in #468.
`deficit` (|r| two-sided, max(0, -r) lower bound) is the worsening measure, so
moving further above a lower bound is never shown as a worse residual.
"""
from .bounds import constrained_state, deficit


def evaluate(target, observation):
    rows = {}
    for key, desired in target["values"].items():
        actual = observation["actual"][key]
        residual = actual - desired
        u = target["uncertainty"][key] + observation["uncertainty"][key]
        t = target["tolerances"][key]
        lower = key in (target.get("lower_bound") or {})
        rows[key] = dict(target=desired, actual=actual, residual=residual, tolerance=t,
                         kind="lower_bound" if lower else "two_sided",
                         u_target=target["uncertainty"][key],
                         u_observation=observation["uncertainty"][key], u=u,
                         margin=(residual - u) if lower else (t - abs(residual) - u),
                         deficit=deficit(target, key, residual),
                         state=constrained_state(target, key, residual, u))
    states = [row["state"] for row in rows.values()]
    overall = "OUTSIDE" if "OUTSIDE" in states else "HOLD" if "HOLD" in states else "PASS"
    return dict(overall=overall, counts={s: states.count(s) for s in ("PASS", "HOLD", "OUTSIDE")},
                metrics=rows,
                remeasure=[k for k, r in rows.items() if r["state"] == "HOLD"],
                independent_of_hold=[k for k, r in rows.items() if r["state"] != "HOLD"])
