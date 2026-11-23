"""Correction Contract: compile blueprint groups into #468 targets and gate hand-off.

The Factory (Codex, #468) executes; this module only decides whether a target
may be handed over and records why not. Nothing here edits a native file.
"""
from . import digest_record, matches_digest, target_issues
from .evidence import TARGET_ELIGIBLE


class OperationRegistry:
    """Operations and their qualification evidence (SHA of a real qualification record)."""

    def __init__(self):
        self.ops = {}

    def register(self, op_id, *, kind, qualified, evidence_sha256=None, scope=None, notes=None):
        if qualified and not matches_digest(evidence_sha256):
            raise ValueError(f"{op_id}: qualified operation requires evidence SHA-256")
        self.ops[op_id] = dict(id=op_id, kind=kind, qualified=bool(qualified),
                               evidence_sha256=evidence_sha256, scope=scope, notes=notes)

    def operation(self, op_id):
        op = self.ops.get(op_id)
        if op is None:
            return dict(id=op_id, qualified=False, evidence_sha256=None)
        return dict(id=op["id"], qualified=op["qualified"], evidence_sha256=op["evidence_sha256"])


def build_request(*, target_id, native_sha256, design_sha256, dependency_hashes, asset_id=None,
                  stage=None):
    request = dict(target_id=target_id, source_sha256=native_sha256,
                   reference_sha256=design_sha256, dependency_hashes=dict(dependency_hashes))
    if asset_id:
        request["asset_id"] = asset_id
    if stage:
        request["stage"] = stage
    return request


def compile_target(blueprint, target_id, registry, *, native_sha256, protected_baseline_sha256,
                   dependency_hashes):
    """Return (target, request, engine_issues). target follows #468 exactly."""
    data = blueprint.data
    group = data["groups"][target_id]
    engine_issues = []
    for key, metric in group["metrics"].items():
        if metric["evidence"] not in TARGET_ELIGIBLE:
            engine_issues.append(f"evidence:{key}")
    design_sha = blueprint.digest()
    target = dict(
        target_id=target_id, source_sha256=native_sha256, sha256=design_sha,
        coordinate_system=group["coordinate_system"], units=group["units"],
        projection=group["projection"], measurement_id=group["measurement_id"],
        values={k: m["value"] for k, m in group["metrics"].items()},
        tolerances={k: m["tolerance"] for k, m in group["metrics"].items()},
        uncertainty={k: m["uncertainty"] for k, m in group["metrics"].items()},
        operation=registry.operation(group["operation_id"]),
        protection=dict(scope_id=group["protection_scope_id"],
                        baseline_sha256=protected_baseline_sha256),
        dependency_fingerprint=digest_record(dependency_hashes),
    )
    if group.get("corrections"):
        corrections = {}
        for metric, rule in group["corrections"].items():
            op = registry.operation(rule["operation_id"])
            if not op["qualified"]:
                engine_issues.append(f"correction_unqualified:{metric}")
                continue                      # never forward an unqualified correction
            corrections[metric] = dict(operation_id=op["id"], qualified=True,
                                       evidence_sha256=op["evidence_sha256"],
                                       max_delta=rule["max_delta"], affects=list(rule["affects"]),
                                       requires_pass=list(rule["requires_pass"]))
        if corrections:
            target["corrections"] = corrections
            target["intersection_limit"] = group["intersection_limit"]
    request = build_request(target_id=target_id, native_sha256=native_sha256,
                            design_sha256=design_sha, dependency_hashes=dependency_hashes,
                            asset_id=data["asset_id"])
    return target, request, engine_issues


def handoff(target, request, engine_issues, *, current_dependency_hashes=None,
            current_protected_sha256=None):
    """Decide Factory eligibility. Any mismatch -> factory_ready False (no edit)."""
    issues = list(engine_issues) + target_issues(target, request)
    if current_dependency_hashes is not None and (
            digest_record(current_dependency_hashes) != target["dependency_fingerprint"]):
        issues.append("dependency_changed")
    if current_protected_sha256 is not None and (
            current_protected_sha256 != target["protection"]["baseline_sha256"]):
        issues.append("protected_scope_changed")
    unblock = []
    if "operation_qualification" in issues:
        unblock.append(f"qualify operation {target['operation']['id']} with a real, SHA-recorded "
                       "calibration on a disposable native copy")
    if any(i.startswith("correction_unqualified") for i in issues):
        unblock.append("qualify the named correction operations (measured response, bounds, "
                       "interference) before Factory correction")
    return dict(target_id=target["target_id"], factory_ready=not issues, issues=issues,
                unblock=unblock, target_contract_sha256=digest_record(target),
                design_sha256=target["sha256"], native_sha256=target["source_sha256"],
                operation=target["operation"], protection=target["protection"],
                dependency_fingerprint=target["dependency_fingerprint"],
                corrections=sorted(target.get("corrections", {})))
