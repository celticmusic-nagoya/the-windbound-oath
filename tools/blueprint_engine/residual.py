"""Residual Engine: |r|+u<=t PASS, |r|-u>t OUTSIDE, otherwise HOLD.

Uses #468 metric_state verbatim with u = target uncertainty + observation
uncertainty (the same combination the Factory uses).
"""
from . import metric_state


def evaluate(target, observation):
    rows = {}
    for key, desired in target["values"].items():
        actual = observation["actual"][key]
        residual = actual - desired
        u = target["uncertainty"][key] + observation["uncertainty"][key]
        t = target["tolerances"][key]
        rows[key] = dict(target=desired, actual=actual, residual=residual, tolerance=t,
                         u_target=target["uncertainty"][key],
                         u_observation=observation["uncertainty"][key], u=u,
                         margin=t - abs(residual) - u, state=metric_state(residual, t, u))
    states = [row["state"] for row in rows.values()]
    overall = "OUTSIDE" if "OUTSIDE" in states else "HOLD" if "HOLD" in states else "PASS"
    return dict(overall=overall, counts={s: states.count(s) for s in ("PASS", "HOLD", "OUTSIDE")},
                metrics=rows,
                remeasure=[k for k, r in rows.items() if r["state"] == "HOLD"],
                independent_of_hold=[k for k, r in rows.items() if r["state"] != "HOLD"])
