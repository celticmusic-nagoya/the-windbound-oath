"""Metric judgement shared with the #468 contract, including one-sided lower bounds.

If the #468 contract provides `constrained_state`/`deficit`/`lower_bound_issues`
(proposal: proposals/468-lower-bound.patch), those are used, so the engine display,
#468 observation check and Factory correction monitor share one implementation.
Until then the reference functions below (identical text to the patch) are used
for display only, and hand-off of lower-bound targets is refused
(`contract_extension_required:lower_bound`).
Two-sided metrics always use #468 `metric_state` unchanged.
"""
import shared_blueprint_contract as _c

from . import finite, metric_state

CONTRACT_SUPPORTS_LOWER_BOUND = all(hasattr(_c, n) for n in
                                    ("constrained_state", "deficit", "lower_bound_issues"))


def _constrained_state(target, key, residual, uncertainty):
    if key in (target.get("lower_bound") or {}):
        if residual - uncertainty >= 0:
            return "PASS"
        if residual + uncertainty < 0:
            return "OUTSIDE"
        return "HOLD"
    return metric_state(residual, target["tolerances"][key], uncertainty)


def _deficit(target, key, residual):
    if key in (target.get("lower_bound") or {}):
        return max(0.0, -residual)
    return abs(residual)


def _lower_bound_issues(target):
    bounds = target.get("lower_bound")
    if bounds is None:
        return []
    values = target.get("values")
    tolerances = target.get("tolerances")
    if (not isinstance(bounds, dict) or not bounds or not isinstance(values, dict)
            or not isinstance(tolerances, dict)):
        return ["lower_bound"]
    corrections = target.get("corrections") or {}
    if not isinstance(corrections, dict):
        return ["lower_bound"]
    issues = []
    for key, lower in bounds.items():
        if (key not in values or not finite(lower) or lower != values[key]
                or tolerances.get(key) != 0 or key in corrections):
            issues.append("lower_bound:" + str(key))
    return issues


if CONTRACT_SUPPORTS_LOWER_BOUND:
    constrained_state, deficit, lower_bound_issues = (_c.constrained_state, _c.deficit,
                                                      _c.lower_bound_issues)
else:
    constrained_state, deficit, lower_bound_issues = (_constrained_state, _deficit,
                                                      _lower_bound_issues)

REFERENCE = dict(constrained_state=_constrained_state, deficit=_deficit,
                 lower_bound_issues=_lower_bound_issues)
