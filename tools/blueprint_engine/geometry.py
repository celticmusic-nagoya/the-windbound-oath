"""Geometry Blueprint: structured, provenance-labelled design information.

Elements describe what is known (landmarks, dimensions, sections, connections,
material regions, mesh/UV/rig specs). Target groups bind metrics that share one
coordinate system, unit and projection into an executable #468 target.

Guard rails enforced here (not left to callers):
* 2D sources cannot assert 3D or hidden values as measured or estimated.
* UNDETERMINED carries no value; every other class carries value + uncertainty.
* RECONSTRUCTED requires a named method and at least two registered views.
"""
import copy
import math

from . import SCHEMA, ENGINE_VERSION, digest_record, finite, present
from .evidence import (CLASSES, MEASURED, PROVISIONAL_DESIGN, RECONSTRUCTED, TARGET_ELIGIBLE,
                       UNDETERMINED, VISIBILITY)

KINDS = ("landmark", "dimension", "section", "silhouette", "connection", "material_region",
         "mesh_spec", "uv_spec", "rig_spec", "anchor", "bounds")


class BlueprintError(ValueError):
    pass


def _numbers(value):
    if finite(value):
        return [value]
    if isinstance(value, list) and value and all(finite(v) for v in value):
        return value
    return None


class Blueprint:
    def __init__(self, *, blueprint_id, asset_id, stage, status, canon_status):
        for name, value in (("blueprint_id", blueprint_id), ("asset_id", asset_id),
                            ("stage", stage), ("status", status), ("canon_status", canon_status)):
            if not present(value):
                raise BlueprintError(f"{name} required")
        self.data = dict(schema=SCHEMA, engine_version=ENGINE_VERSION, blueprint_id=blueprint_id,
                         asset_id=asset_id, stage=stage, status=status,
                         canon_status=canon_status, sources={}, elements={}, groups={},
                         open_questions=[])

    # -- sources -----------------------------------------------------------------
    def add_source(self, record):
        sid = record["source_id"]
        if sid in self.data["sources"]:
            raise BlueprintError(f"duplicate source {sid}")
        self.data["sources"][sid] = copy.deepcopy(record)

    # -- elements ----------------------------------------------------------------
    def add_element(self, *, element_id, kind, module, sources, evidence, coordinate_system,
                    units, dims, value, uncertainty=None, visibility="visible", method=None,
                    notes=None):
        if element_id in self.data["elements"]:
            raise BlueprintError(f"duplicate element {element_id}")
        if kind not in KINDS or evidence not in CLASSES or visibility not in VISIBILITY:
            raise BlueprintError(f"{element_id}: bad kind/evidence/visibility")
        if not sources or any(s not in self.data["sources"] for s in sources):
            raise BlueprintError(f"{element_id}: unregistered source")
        src_dims = {self.data["sources"][s]["dims"] for s in sources}
        if evidence == UNDETERMINED:
            if value is not None:
                raise BlueprintError(f"{element_id}: UNDETERMINED must not carry a value")
        else:
            nums = _numbers(value)
            if nums is None:
                raise BlueprintError(f"{element_id}: value must be finite number(s)")
            if dims in (2, 3) and len(nums) not in (1, dims, 2 * dims):
                raise BlueprintError(f"{element_id}: value arity does not match dims")
            if not finite(uncertainty) or uncertainty < 0:
                raise BlueprintError(f"{element_id}: non-negative uncertainty required")
            if dims == 3 and src_dims and max(src_dims) == 2:
                # 3D value from images only: allowed solely as an explicit design choice
                # or a multi-view reconstruction with a named method.
                if evidence == RECONSTRUCTED:
                    if not present(method) or len(sources) < 2:
                        raise BlueprintError(f"{element_id}: reconstruction needs method + >=2 views")
                elif evidence != PROVISIONAL_DESIGN:
                    raise BlueprintError(f"{element_id}: 2D source cannot assert a 3D {evidence} value")
            if evidence in MEASURED and visibility in ("occluded", "hidden", "estimated"):
                raise BlueprintError(f"{element_id}: {visibility} geometry cannot be {evidence}")
            if evidence == RECONSTRUCTED and not present(method):
                raise BlueprintError(f"{element_id}: RECONSTRUCTED requires method")
        self.data["elements"][element_id] = dict(
            kind=kind, module=module, sources=list(sources), evidence=evidence,
            coordinate_system=coordinate_system, units=units, dims=dims, value=value,
            uncertainty=uncertainty, visibility=visibility, method=method, notes=notes)

    def add_question(self, question_id, text, blocks):
        self.data["open_questions"].append(dict(id=question_id, text=text, blocks=list(blocks)))

    # -- target groups -------------------------------------------------------------
    def add_group(self, *, target_id, measurement_id, coordinate_system, units, projection,
                  metrics, operation_id, protection_scope_id, tolerance_basis, corrections=None,
                  intersection_limit=None, notes=None):
        """metrics: {key: dict(element, select, value, tolerance, uncertainty, evidence[, bound])}

        bound="lower": value is the lower bound L, tolerance must be 0 (one-sided,
        r = x - L; PASS iff r - u >= 0). No other bound kinds are accepted; an
        upper end is never invented.
        """
        if target_id in self.data["groups"]:
            raise BlueprintError(f"duplicate target {target_id}")
        if not metrics:
            raise BlueprintError(f"{target_id}: no metrics")
        for key, metric in metrics.items():
            element = self.data["elements"].get(metric.get("element"))
            if element is None:
                raise BlueprintError(f"{target_id}.{key}: unknown element")
            if metric.get("evidence") not in TARGET_ELIGIBLE or element["evidence"] == UNDETERMINED:
                raise BlueprintError(f"{target_id}.{key}: UNDETERMINED cannot be a target")
            for field in ("value", "tolerance", "uncertainty"):
                if not finite(metric.get(field)) or (field != "value" and metric[field] < 0):
                    raise BlueprintError(f"{target_id}.{key}: invalid {field}")
            bound = metric.get("bound")
            if bound not in (None, "lower"):
                raise BlueprintError(f"{target_id}.{key}: unsupported bound {bound!r}")
            if bound == "lower" and metric["tolerance"] != 0:
                raise BlueprintError(f"{target_id}.{key}: lower bound requires tolerance 0")
            if bound == "lower" and corrections and key in corrections:
                raise BlueprintError(f"{target_id}.{key}: lower-bound metric cannot be auto-corrected")
            if element["coordinate_system"] != coordinate_system or element["units"] != units:
                raise BlueprintError(f"{target_id}.{key}: element context differs from group")
        self.data["groups"][target_id] = dict(
            measurement_id=measurement_id, coordinate_system=coordinate_system, units=units,
            projection=projection, metrics=copy.deepcopy(metrics), operation_id=operation_id,
            protection_scope_id=protection_scope_id, tolerance_basis=tolerance_basis,
            corrections=copy.deepcopy(corrections), intersection_limit=intersection_limit,
            notes=notes)

    # -- output --------------------------------------------------------------------
    def element_value(self, element_id, select=None):
        value = self.data["elements"][element_id]["value"]
        return value if select is None else value[select]

    def to_dict(self):
        return copy.deepcopy(self.data)

    def digest(self):
        return digest_record(self.data)

    def summary(self):
        counts = {c: 0 for c in CLASSES}
        for element in self.data["elements"].values():
            counts[element["evidence"]] += 1
        return dict(blueprint_id=self.data["blueprint_id"], sha256=self.digest(),
                    elements=len(self.data["elements"]), groups=len(self.data["groups"]),
                    evidence_counts=counts, open_questions=len(self.data["open_questions"]))


def span(a, b):
    return math.dist(a, b)
