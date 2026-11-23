"""Measurement Engine and #468 Factory adapters (read-only measurement stages).

An adapter measures a native/official file and returns an observation in the
exact #468 envelope. It never edits; edit/correction operations belong to the
owning asset adapter and are executed by the Codex Factory.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from . import digest_record, finite
from .sources import file_sha256

HERE = Path(__file__).resolve().parent
BLENDER_SCRIPT = HERE / "measure_blender.py"
OBSERVATION_CONTEXT = ("target_id", "source_sha256", "coordinate_system", "units", "projection",
                       "measurement_id", "dependency_fingerprint")


def _write_evidence(native, label, record):
    path = Path(native).parent / f"measure-{label}-{time.monotonic_ns()}.json"
    path.write_text(json.dumps(record, sort_keys=True, indent=1, allow_nan=False) + "\n")
    return path


class _Adapter:
    """Common observation builder; subclasses implement raw()/value()/protected()."""
    method = None

    def __init__(self, selectors, protected_scope_id):
        self.selectors = selectors          # metric key -> selector tuple
        self.protected_scope_id = protected_scope_id
        self.evidence_files = {}

    def build_observation(self, native, target, raw, label):
        actual, uncertainty = {}, {}
        for key in target["values"]:
            value, u = self.value(raw, self.selectors[key])
            actual[key], uncertainty[key] = value, u
        record = dict(method=self.method, native_sha256=file_sha256(native), raw=raw,
                      actual=actual, uncertainty=uncertainty)
        evidence = _write_evidence(native, label, record)
        self.evidence_files[evidence.name] = file_sha256(evidence)
        observation = {key: target[key] for key in OBSERVATION_CONTEXT}
        observation.update(
            operation_id=target["operation"]["id"], native_sha256=record["native_sha256"],
            evidence_sha256=self.evidence_files[evidence.name],
            protected_scope_id=self.protected_scope_id,
            protected_sha256=self.protected(native, raw), actual=actual,
            residuals={k: actual[k] - target["values"][k] for k in actual},
            uncertainty=uncertainty, target_contract_sha256=digest_record(target))
        if target.get("corrections") is not None:
            observation["intersections"] = raw.get("intersections", 0)
        return observation

    # #468 Factory adapter interface (read-only stage: measure / finish / reopen)
    def measure(self, native, target, *, deadline=None):
        return self.build_observation(native, target, self.raw(native, deadline), "measure")

    def reopen(self, native, target, *, deadline=None):
        # Fresh read in a new process/handle; nothing cached from measure().
        return self.build_observation(native, target, self.raw(native, deadline), "reopen")

    def finish(self, native, target, *, deadline=None):
        return dict(self.evidence_files)

    def edit(self, *args, **kwargs):
        raise RuntimeError("Blueprint Engine measurement adapters are read-only")

    correct = propose_correction = correct_metric = edit


class ImageAlphaAdapter(_Adapter):
    """Pixel-exact alpha-silhouette measurement on an SHA-verified official image.

    Selectors: ("bbox", i) -> alpha bbox xyxy[i]; ("scan", y, "left"|"right").
    Inclusive integer bounds at alpha >= threshold; uncertainty 0 for this definition.
    """
    method = "pil-alpha-threshold-inclusive-bounds"

    def __init__(self, selectors, protected_scope_id, threshold=128):
        super().__init__(selectors, protected_scope_id)
        self.threshold = threshold

    def raw(self, native, deadline=None):
        with Image.open(native) as image:
            image.load()
            alpha = image.getchannel("A")
            width, height = image.size
        mask = alpha.point(lambda a: 255 if a >= self.threshold else 0)
        bbox = mask.getbbox()
        rows = {}
        for selector in self.selectors.values():
            if selector[0] == "scan" and selector[1] not in rows:
                y = selector[1]
                xs = [x for x in range(width) if mask.getpixel((x, y))]
                rows[y] = [xs[0], xs[-1]] if xs else None
        return dict(size=[width, height], threshold=self.threshold,
                    bbox_xyxy=[bbox[0], bbox[1], bbox[2] - 1, bbox[3] - 1] if bbox else None,
                    scanlines={str(y): v for y, v in rows.items()})

    def value(self, raw, selector):
        if selector[0] == "bbox":
            return float(raw["bbox_xyxy"][selector[1]]), 0.0
        bounds = raw["scanlines"][str(selector[1])]
        if bounds is None:
            raise ValueError(f"no alpha pixels on scanline y={selector[1]}")
        return float(bounds[0 if selector[2] == "left" else 1]), 0.0

    def protected(self, native, raw):
        return file_sha256(native)          # the whole official image is protected


class BlenderAdapter(_Adapter):
    """Native Blender measurement through measure_blender.py in a separate process.

    Selectors: ("bounds", [objects], "min"|"max", axis) union world bbox;
               ("anchor", name, axis) world translation;
               ("gap", low_object, high_object, axis) clearance between two bboxes.
    Uncertainty: float32 storage bound 2**-22 * max(1, |v|) per coordinate.
    Protected fingerprint: SHA-256 over per-object fingerprints of protect_objects
    (None = every object in the scene).
    """
    method = "bpy-world-mesh-bbox-and-object-translation"

    def __init__(self, selectors, protected_scope_id, protect_objects=None, python=None,
                 timeout=600, evaluated=False, components=()):
        super().__init__(selectors, protected_scope_id)
        self.protect_objects = protect_objects
        self.python = python or [sys.executable, "-I"]
        self.timeout = timeout
        self.evaluated = evaluated
        self.components = list(components)

    def raw(self, native, deadline=None):
        out_dir = Path(native).parent
        spec = out_dir / f"spec-{time.monotonic_ns()}.json"
        out = out_dir / f"raw-{time.monotonic_ns()}.json"
        spec.write_text(json.dumps(dict(evaluated=self.evaluated, components=self.components)))
        timeout = self.timeout if deadline is None else max(1, min(self.timeout,
                                                                   deadline - time.monotonic()))
        before = file_sha256(native)
        proc = subprocess.run([*self.python, str(BLENDER_SCRIPT), str(native), str(spec), str(out)],
                              capture_output=True, text=True, timeout=timeout,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        if proc.returncode != 0 or not out.is_file():
            raise RuntimeError("blender measurement failed: " + proc.stderr[-2000:])
        if file_sha256(native) != before:
            raise RuntimeError("blender measurement modified the native file")
        raw = json.loads(out.read_text())
        spec.unlink()
        out.unlink()
        if raw.get("is_dirty"):
            raise RuntimeError("native reported dirty state after read-only open")
        return raw

    def value(self, raw, selector):
        objects = raw["objects"]
        if selector[0] == "anchor":
            value = objects[selector[1]]["location"][selector[2]]
        elif selector[0] == "gap":
            # ("gap", low_object, high_object, axis): high.bbox_min - low.bbox_max
            low, high, axis = selector[1], selector[2], selector[3]
            value = objects[high]["bbox_min"][axis] - objects[low]["bbox_max"][axis]
            if not finite(value):
                raise ValueError("non-finite native measurement")
            u = 2.0 ** -22 * (max(1.0, abs(objects[high]["bbox_min"][axis]))
                              + max(1.0, abs(objects[low]["bbox_max"][axis])))
            return value, u
        else:
            names, side, axis = selector[1], selector[2], selector[3]
            missing = [n for n in names if n not in objects or "bbox_min" not in objects[n]]
            if missing:
                raise KeyError("measurement objects missing: " + ", ".join(missing))
            pick = min if side == "min" else max
            value = pick(objects[n]["bbox_" + side][axis] for n in names)
        if not finite(value):
            raise ValueError("non-finite native measurement")
        return value, 2.0 ** -22 * max(1.0, abs(value))

    def protected(self, native, raw):
        names = sorted(raw["objects"] if self.protect_objects is None else self.protect_objects)
        missing = [n for n in names if n not in raw["objects"]]
        if missing:
            return "0" * 64                 # fail closed: protected object disappeared
        return hashlib.sha256("".join(raw["objects"][n]["fingerprint"] for n in names)
                              .encode()).hexdigest()


def baseline_protected_sha(adapter, native):
    """Measure the protected fingerprint of the registered source before any stage."""
    return adapter.protected(native, adapter.raw(native))


class VrmFaceAdapter(_Adapter):
    """Read-only VRoid face measurement (measure_vrm_face.py) on a Blender-imported VRM.

    Selectors: metric name -> ratio to head height (dimensionless). Native numeric
    uncertainty is float32 storage only; definition differences against the
    illustration are carried by the blueprint (target uncertainty / comparability).
    Protected scope: the whole native file (read-only stage).
    """
    method = "bpy-vroid-material-region-front-ortho-ratio"
    script = HERE / "measure_vrm_face.py"

    def __init__(self, selectors, protected_scope_id, python=None, timeout=600):
        super().__init__(selectors, protected_scope_id)
        self.python = python or [sys.executable, "-I"]
        self.timeout = timeout

    def raw(self, native, deadline=None):
        out_dir = Path(native).parent
        spec = out_dir / f"spec-{time.monotonic_ns()}.json"
        out = out_dir / f"raw-{time.monotonic_ns()}.json"
        spec.write_text("{}")
        before = file_sha256(native)
        timeout = self.timeout if deadline is None else max(1, min(self.timeout,
                                                                   deadline - time.monotonic()))
        proc = subprocess.run([*self.python, str(self.script), str(native), str(spec), str(out)],
                              capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0 or not out.is_file():
            raise RuntimeError("vrm face measurement failed: " + (proc.stderr + proc.stdout)[-2000:])
        if file_sha256(native) != before:
            raise RuntimeError("vrm face measurement modified the native file")
        raw = json.loads(out.read_text())
        spec.unlink()
        out.unlink()
        if raw.get("is_dirty") or raw.get("nonzero_shape_keys"):
            raise RuntimeError("face not in basis/clean state: " + repr(raw.get("nonzero_shape_keys")))
        return raw

    def value(self, raw, selector):
        value = raw["ratios"][selector]
        if not finite(value):
            raise ValueError(f"face metric {selector} not measurable")
        return value, 2.0 ** -22 * 4

    def protected(self, native, raw):
        return file_sha256(native)
