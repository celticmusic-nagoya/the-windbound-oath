"""Validate the shared target envelope around owner-specific measurement adapters.

Adapters retain their registration, native measurement and correction logic.
This contract binds their evidence to one immutable target and dependency set.
"""
import hashlib
import json
import math
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def matches_digest(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def present(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def digest_record(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def metric_map(values, keys, *, nonnegative=False):
    return (isinstance(values, dict) and values.keys() == keys
            and all(finite(value) and (not nonnegative or value >= 0)
                    for value in values.values()))


def metric_state(residual, tolerance, uncertainty):
    magnitude = abs(residual)
    if magnitude + uncertainty <= tolerance:
        return "PASS"
    if magnitude - uncertainty > tolerance:
        return "OUTSIDE"
    return "HOLD"


def constrained_state(target, key, residual, uncertainty):
    """Shared judgement for one metric (#468 Factory, observation check, #485 display).

    Two-sided (default, unchanged): metric_state(|r|, t, u).
    Lower bound (key in target["lower_bound"], L = values[key], r = x - L):
    r - u >= 0 PASS, r + u < 0 OUTSIDE, otherwise HOLD.
    """
    if key in (target.get("lower_bound") or {}):
        if residual - uncertainty >= 0:
            return "PASS"
        if residual + uncertainty < 0:
            return "OUTSIDE"
        return "HOLD"
    return metric_state(residual, target["tolerances"][key], uncertainty)


def deficit(target, key, residual):
    """Distance from acceptance used to detect worsening; moving further above a
    lower bound is never a worsening."""
    if key in (target.get("lower_bound") or {}):
        return max(0.0, -residual)
    return abs(residual)


def lower_bound_issues(target):
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


def target_issues(target, request):
    if not isinstance(target, dict) or not matches_digest(target.get("sha256")) or (
            target["sha256"] != request.get("reference_sha256")):
        return ["design"]

    issues = []
    if not present(target.get("target_id")) or target["target_id"] != request.get("target_id"):
        issues.append("target_id")
    if not matches_digest(target.get("source_sha256")) or target["source_sha256"] != request.get("source_sha256"):
        issues.append("design_source_sha256")
    if not all(present(target.get(field)) for field in ("coordinate_system", "units", "projection", "measurement_id")):
        issues.append("measurement_context")
    values = target.get("values")
    if (not isinstance(values, dict) or not values or not all(present(key) for key in values)
            or not metric_map(values, values.keys())):
        issues.append("design_values")
    else:
        if not metric_map(target.get("tolerances"), values.keys(), nonnegative=True):
            issues.append("design_tolerances")
        if not metric_map(target.get("uncertainty"), values.keys(), nonnegative=True):
            issues.append("design_uncertainty")
    operation = target.get("operation")
    if (not isinstance(operation, dict) or not present(operation.get("id"))
            or operation.get("qualified") is not True
            or not matches_digest(operation.get("evidence_sha256"))):
        issues.append("operation_qualification")
    corrections = target.get("corrections")
    if corrections is not None:
        keys = set(values) if isinstance(values, dict) else set()
        if (not isinstance(corrections, dict) or not corrections or not corrections.keys() <= keys
                or type(target.get("intersection_limit")) is not int
                or target["intersection_limit"] < 0):
            issues.append("correction_qualification")
        else:
            for metric, rule in corrections.items():
                if (not isinstance(rule, dict) or not present(rule.get("operation_id"))
                        or rule.get("qualified") is not True
                        or not matches_digest(rule.get("evidence_sha256"))
                        or not finite(rule.get("max_delta")) or rule["max_delta"] <= 0
                        or not isinstance(rule.get("affects"), list)
                        or not isinstance(rule.get("requires_pass"), list)
                        or not all(present(key) and key in keys for key in
                                   rule["affects"] + rule["requires_pass"])
                        or metric not in rule["affects"] or metric in rule["requires_pass"]):
                    issues.append("correction_qualification:" + metric)
    protected = target.get("protection")
    if (not isinstance(protected, dict) or not present(protected.get("scope_id"))
            or not matches_digest(protected.get("baseline_sha256"))):
        issues.append("protected_scope")
    issues += lower_bound_issues(target)
    dependencies = request.get("dependency_hashes")
    if (not isinstance(dependencies, dict)
            or not all(present(key) and matches_digest(value) for key, value in dependencies.items())
            or target.get("dependency_fingerprint") != digest_record(dependencies)):
        issues.append("dependency_fingerprint")
    return issues


def measurement_issues(target, request, observation):
    """Check adapter-emitted residuals and protection before accepting a native result."""
    issues = target_issues(target, request)
    if issues:
        return issues
    if not isinstance(observation, dict) or any(
        observation.get(field) != target[field] for field in
        ("target_id", "source_sha256", "coordinate_system", "units", "projection",
         "measurement_id", "dependency_fingerprint")
    ) or observation.get("operation_id") != target["operation"]["id"] or (
        observation.get("target_contract_sha256") != digest_record(target)
    ):
        return ["observation_context"]
    if not matches_digest(observation.get("native_sha256")) or not matches_digest(observation.get("evidence_sha256")):
        issues.append("measurement_evidence")
    if (observation.get("protected_scope_id") != target["protection"]["scope_id"]
            or observation.get("protected_sha256") != target["protection"]["baseline_sha256"]):
        issues.append("protected_scope")
    if target.get("corrections") is not None and (
        type(observation.get("intersections")) is not int
        or not 0 <= observation["intersections"] <= target["intersection_limit"]
    ):
        issues.append("intersections")
    values = target["values"]
    actual, residuals, uncertainty = (observation.get(key) for key in ("actual", "residuals", "uncertainty"))
    if not (metric_map(actual, values.keys()) and metric_map(residuals, values.keys())
            and metric_map(uncertainty, values.keys(), nonnegative=True)):
        return issues + ["measurement_values"]
    for key, desired in values.items():
        expected = actual[key] - desired
        if not finite(expected) or not math.isclose(residuals[key], expected, rel_tol=1e-9, abs_tol=1e-12):
            issues.append(f"residual:{key}")
        elif constrained_state(target, key, expected,
                               uncertainty[key] + target["uncertainty"][key]) != "PASS":
            issues.append(f"tolerance:{key}")
    return issues
