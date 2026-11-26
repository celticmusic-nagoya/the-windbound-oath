"""Blueprint Engine tests: guards, residual law, #468 contract compatibility, adapters.

Run from tools/:  python3 -m unittest discover -s blueprint_engine/tests -t .
Blender tests run when `bpy` (5.3.0) is importable; otherwise they are skipped.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
import zipfile

from PIL import Image

from blueprint_engine import digest_record, measurement_issues, metric_state, target_issues
from blueprint_engine.contract import OperationRegistry, compile_target, handoff
from blueprint_engine.evidence import (ESTIMATED, NATIVE_MEASURED, OFFICIAL_SOURCE_MEASURED,
                                       PROVISIONAL_DESIGN, RECONSTRUCTED, UNDETERMINED)
from blueprint_engine.export import ledger
from blueprint_engine.geometry import Blueprint, BlueprintError
from blueprint_engine.measure import BlenderAdapter, ImageAlphaAdapter, baseline_protected_sha
from blueprint_engine.residual import evaluate
from blueprint_engine.sources import file_sha256, register_source
from shared_factory_stage import execute_factory_stage

HAS_BPY = importlib.util.find_spec("bpy") is not None
Q = "1" * 64


def png(path, box=(10, 20, 30, 60), size=(64, 96)):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    for x in range(box[0], box[2] + 1):
        for y in range(box[1], box[3] + 1):
            image.putpixel((x, y), (200, 100, 50, 255))
    image.save(path)
    return path


def image_blueprint(src, value=10.0):
    bp = Blueprint(blueprint_id="t", asset_id="T", stage="s", status="TEST", canon_status="TEST")
    bp.add_source(register_source(src, source_id="img", role="OFFICIAL_CANON",
                                  projection="image-2d-uncalibrated", coordinate_system="px",
                                  units="px", provenance="test", license="test"))
    bp.add_element(element_id="bbox", kind="silhouette", module="body", sources=["img"],
                   evidence=OFFICIAL_SOURCE_MEASURED, coordinate_system="px", units="px", dims=2,
                   value=[10, 20, 30, 60], uncertainty=0.0)
    bp.add_group(target_id="g", measurement_id="alpha", coordinate_system="px", units="px",
                 projection="image-2d-uncalibrated", operation_id="m",
                 protection_scope_id="img.file", tolerance_basis="test",
                 metrics={"x0": dict(element="bbox", value=value, tolerance=0.0,
                                     uncertainty=0.0, evidence=OFFICIAL_SOURCE_MEASURED),
                          "y1": dict(element="bbox", value=60.0, tolerance=0.0,
                                     uncertainty=0.0, evidence=OFFICIAL_SOURCE_MEASURED)})
    return bp


def registry(qualified=True):
    r = OperationRegistry()
    r.register("m", kind="read_only_measure", qualified=qualified,
               evidence_sha256=Q if qualified else None)
    return r


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.dir = TemporaryDirectory()
        self.src = png(Path(self.dir.name) / "a.png")
        self.bp = Blueprint(blueprint_id="t", asset_id="T", stage="s", status="TEST",
                            canon_status="TEST")
        for sid in ("front", "side"):
            self.bp.add_source(register_source(self.src, source_id=sid, role="REFERENCE",
                                               projection="orthographic-2d",
                                               coordinate_system="px", units="px",
                                               provenance="test", license="test"))

    def tearDown(self):
        self.dir.cleanup()

    def element(self, **kw):
        base = dict(element_id="e", kind="landmark", module="face", sources=["front"],
                    evidence=ESTIMATED, coordinate_system="px", units="px", dims=2,
                    value=[1, 2], uncertainty=1.0)
        base.update(kw)
        self.bp.add_element(**base)

    def test_2d_source_cannot_assert_3d_measured_or_estimated(self):
        for evidence in (ESTIMATED, OFFICIAL_SOURCE_MEASURED, NATIVE_MEASURED):
            with self.subTest(evidence=evidence), self.assertRaises(BlueprintError):
                self.element(element_id=evidence, evidence=evidence, dims=3, value=[1, 2, 3])

    def test_3d_from_2d_only_as_named_multiview_reconstruction_or_design(self):
        with self.assertRaises(BlueprintError):
            self.element(element_id="r1", evidence=RECONSTRUCTED, dims=3, value=[1, 2, 3])
        with self.assertRaises(BlueprintError):
            self.element(element_id="r2", evidence=RECONSTRUCTED, dims=3, value=[1, 2, 3],
                         method="ortho triangulation")
        self.element(element_id="r3", evidence=RECONSTRUCTED, dims=3, value=[1, 2, 3],
                     method="ortho triangulation", sources=["front", "side"])
        self.element(element_id="d", evidence=PROVISIONAL_DESIGN, dims=3, value=[1, 2, 3])

    def test_undetermined_and_hidden_rules(self):
        with self.assertRaises(BlueprintError):
            self.element(element_id="u", evidence=UNDETERMINED)
        self.element(element_id="u2", evidence=UNDETERMINED, value=None, visibility="occluded")
        with self.assertRaises(BlueprintError):
            self.element(element_id="h", evidence=OFFICIAL_SOURCE_MEASURED, visibility="occluded",
                         uncertainty=0.0)
        with self.assertRaises(BlueprintError):
            self.bp.add_group(target_id="g", measurement_id="m", coordinate_system="px",
                              units="px", projection="orthographic-2d", operation_id="m",
                              protection_scope_id="p", tolerance_basis="t",
                              metrics={"k": dict(element="u2", value=1.0, tolerance=1.0,
                                                 uncertainty=0.0, evidence=ESTIMATED)})

    def test_unregistered_source_and_sha_mismatch_fail_closed(self):
        with self.assertRaises(BlueprintError):
            self.element(sources=["missing"])
        with self.assertRaises(ValueError):
            register_source(self.src, source_id="x", role="REFERENCE",
                            projection="orthographic-2d", coordinate_system="px", units="px",
                            provenance="t", license="t", expected_sha256="0" * 64)

    def test_unsafe_archive_member_rejected(self):
        bad = Path(self.dir.name) / "bad.vroid"
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../escape.bin", b"x")
        with self.assertRaises(ValueError):
            register_source(bad, source_id="v", role="NATIVE_WORKING", projection="native-3d",
                            coordinate_system="v", units="UNKNOWN", provenance="t", license="t")


class ResidualTests(unittest.TestCase):
    def test_law_matches_468_metric_state_at_boundaries(self):
        # dyadic values: boundaries are exact in binary floating point
        cases = [(0.25, .5, .25, "PASS"), (0.875, .5, .25, "OUTSIDE"), (0.5, .5, .125, "HOLD"),
                 (-0.75, .5, .25, "HOLD"), (-0.8125, .5, .25, "OUTSIDE"), (0, 0, 0, "PASS")]
        for r, t, u, expected in cases:
            target = dict(values={"k": 0.0}, tolerances={"k": t}, uncertainty={"k": u / 2})
            obs = dict(actual={"k": r}, uncertainty={"k": u / 2})
            report = evaluate(target, obs)
            with self.subTest(r=r):
                self.assertEqual(report["metrics"]["k"]["state"], metric_state(r, t, u))
                self.assertEqual(report["overall"], expected)

    def test_direct_residual_refuses_invalid_metric_maps(self):
        target = dict(values={"k": 0.0}, tolerances={"k": 0.5}, uncertainty={"k": 0.1})
        obs = dict(actual={"k": 0.25}, uncertainty={"k": 0.1})
        for field, bad in (
            ("values", {}), ("values", {"": 0}), ("values", {"k": True}),
            ("tolerances", {"k": -0.5}), ("uncertainty", {"k": -1.0}),
            ("uncertainty", {"k": float("nan")}), ("tolerances", {"k": float("inf")}),
            ("lower_bound", {"k": 1.0}), ("lower_bound", []),
            ("tolerances", {"k": 0.5, "other": 0}),
        ):
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(ValueError):
                    evaluate(dict(target, **{field: bad}), obs)
        for field, bad in (
            ("actual", {}), ("actual", {"k": float("nan")}),
            ("actual", {"k": True}), ("actual", {"k": 0, "other": 0}),
            ("uncertainty", {"k": -1}), ("uncertainty", {"k": float("inf")}),
        ):
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(ValueError):
                    evaluate(target, dict(obs, **{field: bad}))

    def test_direct_residual_refuses_arithmetic_overflow(self):
        target = dict(values={"k": -1e308}, tolerances={"k": 0.5}, uncertainty={"k": 0.0})
        obs = dict(actual={"k": 1e308}, uncertainty={"k": 0.0})
        with self.assertRaises(ValueError):
            evaluate(target, obs)
        target["values"]["k"] = 1e308
        target["uncertainty"]["k"] = obs["uncertainty"]["k"] = 1e308
        with self.assertRaises(ValueError):
            evaluate(target, obs)

    def test_direct_residual_valid_lower_bound(self):
        target = dict(values={"k": 1.0}, tolerances={"k": 0}, uncertainty={"k": 0.125},
                      lower_bound={"k": 1.0})
        for actual, expected in ((1.25, "PASS"), (1.0, "HOLD"), (0.625, "OUTSIDE")):
            with self.subTest(actual=actual):
                obs = dict(actual={"k": actual}, uncertainty={"k": 0.125})
                self.assertEqual(evaluate(target, obs)["overall"], expected)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.dir = TemporaryDirectory()
        self.src = png(Path(self.dir.name) / "a.png")
        self.sha = file_sha256(self.src)
        self.deps = {"design": "2" * 64}

    def tearDown(self):
        self.dir.cleanup()

    def compile(self, bp=None, reg=None):
        return compile_target(bp or image_blueprint(self.src), "g", reg or registry(),
                              native_sha256=self.sha, protected_baseline_sha256=self.sha,
                              dependency_hashes=self.deps)

    def test_compiled_target_is_468_valid(self):
        target, request, issues = self.compile()
        self.assertEqual(issues, [])
        self.assertEqual(target_issues(target, request), [])
        self.assertTrue(handoff(target, request, issues)["factory_ready"])

    def test_unqualified_operation_blocks_handoff(self):
        target, request, issues = self.compile(reg=registry(False))
        gate = handoff(target, request, issues)
        self.assertFalse(gate["factory_ready"])
        self.assertIn("operation_qualification", gate["issues"])
        self.assertTrue(gate["unblock"])

    def test_dependency_or_protection_change_blocks_handoff(self):
        target, request, issues = self.compile()
        self.assertIn("dependency_changed", handoff(
            target, request, issues, current_dependency_hashes={"design": "3" * 64})["issues"])
        self.assertIn("protected_scope_changed", handoff(
            target, request, issues, current_protected_sha256="4" * 64)["issues"])

    def test_corrections_forwarded_only_when_qualified(self):
        bp = image_blueprint(self.src)
        bp.data["groups"]["g"].update(corrections={"x0": dict(
            operation_id="move", max_delta=2.0, affects=["x0"], requires_pass=["y1"])},
            intersection_limit=0)
        reg = registry()
        reg.register("move", kind="correction", qualified=False)
        target, request, issues = self.compile(bp, reg)
        self.assertNotIn("corrections", target)
        self.assertIn("correction_unqualified:x0", issues)
        reg.register("move", kind="correction", qualified=True, evidence_sha256=Q)
        target, request, issues = self.compile(bp, reg)
        self.assertEqual((issues, target_issues(target, request)), ([], []))
        self.assertTrue(target["corrections"]["x0"]["qualified"])


class ImageAdapterFactoryTests(unittest.TestCase):
    def run_stage(self, value):
        with TemporaryDirectory() as d:
            root = Path(d)
            src = png(root / "src.png")
            sha = file_sha256(src)
            target, request, _ = compile_target(
                image_blueprint(src, value), "g", registry(), native_sha256=sha,
                protected_baseline_sha256=sha, dependency_hashes={"d": "2" * 64})
            adapter = ImageAlphaAdapter({"x0": ("bbox", 0), "y1": ("bbox", 3)}, "img.file")
            obs = adapter.measure(src, target)
            self.assertEqual(measurement_issues(target, request, obs),
                             [] if value == 10.0 else ["tolerance:x0"])
            stage = dict(id="m", requires_actual_edit=False, fingerprint="f")
            adapter.evidence_files = {}
            (root / "f").mkdir()
            return execute_factory_stage(root / "f", src, stage, target, request, adapter,
                                         time.monotonic() + 60, lambda: None)

    def test_factory_read_only_stage_passes_and_reopens(self):
        cp = self.run_stage(10.0)
        self.assertTrue(cp["reopened"])
        self.assertFalse(cp["requires_actual_edit"])

    def test_factory_blocks_outside_measurement(self):
        with self.assertRaisesRegex(RuntimeError, "tolerance:x0"):
            self.run_stage(11.0)

    def test_adapter_refuses_edits(self):
        adapter = ImageAlphaAdapter({}, "s")
        for name in ("edit", "correct", "propose_correction", "correct_metric"):
            with self.assertRaises(RuntimeError):
                getattr(adapter, name)()

    def test_ledger_records_sha(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text("{}")
            entries = ledger(d)
            self.assertEqual(entries["x.json"]["sha256"], file_sha256(p))
            self.assertIn("x.json", (Path(d) / "SHA256SUMS").read_text())


class MeasurementDeadlineTests(unittest.TestCase):
    def adapters(self):
        from blueprint_engine.measure import VrmFaceAdapter
        return (BlenderAdapter({}, "s"), VrmFaceAdapter({}, "s"))

    def test_expired_deadline_never_launches(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            src.write_bytes(b"fixture")
            for adapter in self.adapters():
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.subprocess.run") as run:
                    with self.assertRaises(TimeoutError):
                        adapter.raw(src, deadline=time.monotonic() - 1)
                    run.assert_not_called()
                    self.assertEqual(list(Path(d).iterdir()), [src])

    def test_timeout_cleans_disposable_process_files(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            src.write_bytes(b"fixture")
            def fail(args, **kwargs):
                self.assertGreater(kwargs["timeout"], 0)
                Path(args[-1]).write_text("partial")
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            for adapter in self.adapters():
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.subprocess.run", side_effect=fail):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        adapter.raw(src, deadline=time.monotonic() + 30)
                    self.assertEqual(list(Path(d).iterdir()), [src])
                    self.assertEqual(src.read_bytes(), b"fixture")

    def test_timeout_with_modified_native_is_integrity_failure(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            def fail(args, **kwargs):
                src.write_bytes(b"unexpected mutation")
                Path(args[-1]).write_text("partial")
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            for adapter in self.adapters():
                src.write_bytes(b"fixture")
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.subprocess.run", side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError, "modified the native file") as caught:
                        adapter.raw(src, deadline=time.monotonic() + 30)
                    self.assertIsInstance(caught.exception.__context__, subprocess.TimeoutExpired)
                    self.assertEqual(src.read_bytes(), b"unexpected mutation")
                    self.assertEqual(list(Path(d).iterdir()), [src])

    def test_timeout_with_missing_native_is_integrity_failure(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            def fail(args, **kwargs):
                src.unlink()
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            for adapter in self.adapters():
                src.write_bytes(b"fixture")
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.subprocess.run", side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError, "native integrity unavailable"):
                        adapter.raw(src, deadline=time.monotonic() + 30)
                    self.assertEqual(list(Path(d).iterdir()), [])

    def test_nonzero_exit_retains_bounded_stdout_and_stderr(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            src.write_bytes(b"fixture")
            def fail(args, **kwargs):
                return subprocess.CompletedProcess(args, 1, "X" * 3000 + " stdout cause", "Y" * 3000 + " stderr cause")
            for adapter in self.adapters():
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.subprocess.run", side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError, "measurement failed") as caught:
                        adapter.raw(src)
                    message = str(caught.exception)
                    self.assertIn("stdout cause", message)
                    self.assertIn("stderr cause", message)
                    self.assertLess(len(message), 4200)
                    self.assertEqual(list(Path(d).iterdir()), [src])

    def test_subsecond_budget_and_success_cleanup(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            src.write_bytes(b"fixture")
            def succeed(args, **kwargs):
                self.assertEqual(kwargs["timeout"], .25)
                Path(args[-1]).write_text('{"is_dirty": false}')
                return subprocess.CompletedProcess(args, 0, "", "")
            for adapter in self.adapters():
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.time.monotonic", return_value=10), patch("blueprint_engine.measure.subprocess.run", side_effect=succeed):
                    self.assertEqual(adapter.raw(src, deadline=10.25), {"is_dirty": False})
                    self.assertEqual(list(Path(d).iterdir()), [src])

    def test_expiry_during_hash_prevents_launch(self):
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            src = Path(d) / "native.blend"
            src.write_bytes(b"fixture")
            for adapter in self.adapters():
                with self.subTest(adapter=adapter.method), patch("blueprint_engine.measure.time.monotonic", side_effect=[10, 11]), patch("blueprint_engine.measure.subprocess.run") as run:
                    with self.assertRaises(TimeoutError):
                        adapter.raw(src, deadline=10.5)
                    run.assert_not_called()
                    self.assertEqual(list(Path(d).iterdir()), [src])


MAKE_BLEND = """
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("m")
mesh.from_pydata([(0,0,0),(1,0,0),(1,2,0),(0,2,0),(0,0,3),(1,0,3),(1,2,3),(0,2,3)], [],
                 [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
box = bpy.data.objects.new("BOX", mesh); bpy.context.scene.collection.objects.link(box)
other = bpy.data.objects.new("OTHER", mesh.copy()); bpy.context.scene.collection.objects.link(other)
other.location = (5, 0, 0)
if sys.argv[-1] == "moved": other.location = (5, 0.5, 0)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-2])
"""


@unittest.skipUnless(HAS_BPY, "bpy 5.3.0 not installed")
class BlenderAdapterTests(unittest.TestCase):
    def make(self, path, variant="base"):
        script = Path(path).with_suffix(".py")
        script.write_text(MAKE_BLEND)
        subprocess.run([sys.executable, "-I", str(script), str(path), variant], check=True,
                       capture_output=True)
        return path

    def test_native_measure_protection_and_factory(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            blend = self.make(root / "a.blend")
            moved = self.make(root / "b.blend", "moved")
            sha = file_sha256(blend)
            bp = Blueprint(blueprint_id="b", asset_id="B", stage="s", status="TEST",
                           canon_status="TEST")
            bp.add_source(register_source(blend, source_id="n", role="NATIVE_WORKING",
                                          projection="native-3d", coordinate_system="w",
                                          units="m", provenance="t", license="t"))
            bp.add_element(element_id="box", kind="bounds", module="m", sources=["n"],
                           evidence=NATIVE_MEASURED, coordinate_system="w", units="m", dims=3,
                           value=[0, 0, 0, 1, 2, 3], uncertainty=0.0)
            bp.add_group(target_id="g", measurement_id="bbox", coordinate_system="w", units="m",
                         projection="native-3d", operation_id="m", protection_scope_id="other",
                         tolerance_basis="t",
                         metrics={"ymax": dict(element="box", value=2.0, tolerance=1e-4,
                                               uncertainty=0.0, evidence=NATIVE_MEASURED)})
            adapter = BlenderAdapter({"ymax": ("bounds", ["BOX"], "max", 1)}, "other",
                                     protect_objects=["OTHER"])
            baseline = baseline_protected_sha(adapter, blend)
            target, request, issues = compile_target(
                bp, "g", registry(), native_sha256=sha, protected_baseline_sha256=baseline,
                dependency_hashes={"d": "2" * 64})
            obs = adapter.measure(blend, target)
            self.assertEqual(measurement_issues(target, request, obs), [])
            self.assertEqual(file_sha256(blend), sha)            # read-only
            self.assertNotEqual(baseline_protected_sha(adapter, moved), baseline)
            adapter.evidence_files = {}
            (root / "f").mkdir()
            cp = execute_factory_stage(root / "f", blend, dict(id="m", requires_actual_edit=False,
                                                               fingerprint="f"),
                                       target, request, adapter, time.monotonic() + 300,
                                       lambda: None)
            self.assertEqual(cp["sha256"], sha)
            # protected object changed -> observation protected mismatch -> fail closed
            target2, request2, _ = compile_target(
                bp, "g", registry(), native_sha256=file_sha256(moved),
                protected_baseline_sha256=baseline, dependency_hashes={"d": "2" * 64})
            self.assertIn("protected_scope",
                          measurement_issues(target2, request2, adapter.measure(moved, target2)))


if __name__ == "__main__":
    unittest.main()


class P1MethodTests(unittest.TestCase):
    def test_porch_classifier_uses_geometry_rules_not_design_values(self):
        from blueprint_engine.cases.lind_home_porch import classify
        box = lambda a, b: dict(bbox_min=a, bbox_max=b, vertices=8)
        parts = classify([box([-1.15, -4.7, 0], [-0.83, -4.39, 0.2]),
                          box([-1.05, -4.6, 0.2], [-0.93, -4.49, 2.4]),
                          box([-1.15, -4.63, 2.4], [1.15, -4.47, 2.56]),
                          box([-1.17, -4.9, 2.5], [1.17, -3.3, 3.3])])
        self.assertEqual([len(parts[k]) for k in ("plinths", "posts", "lintels", "other")],
                         [1, 1, 1, 1])

    def test_face_ratio_uncertainty_budget(self):
        from blueprint_engine.cases.morwen_face_vrm import official
        precision = {"face_front_review": {"points": {
            "left_outer_eye": [169, 120], "left_inner_eye": [201, 120],
            "right_inner_eye": [228, 120], "right_outer_eye": [258, 120],
            "left_iris_center": [188, 125], "right_iris_center": [239, 125],
            "nose_tip": [214, 144], "mouth_left": [206, 159], "mouth_right": [222, 159],
            "chin": [214, 180]}}}
        landmarks = {"views": {"front": {"landmarks": {
            "crown": {"xy_px": [208, 18], "uncertainty_px": 2},
            "chin": {"xy_px": [214, 180], "uncertainty_px": 3}}}}}
        head, u_head, out = official(precision, landmarks)
        self.assertEqual((head, u_head), (162, 5))
        self.assertAlmostEqual(out["eye_width_left"]["u"], 6 / 162 + 32 * 5 / 162 ** 2)
        self.assertGreater(out["eye_width_left"]["u"], out["eye_width_left"]["tolerance"])

    def test_face_adapter_is_read_only(self):
        from blueprint_engine.measure import VrmFaceAdapter
        adapter = VrmFaceAdapter({}, "s")
        for name in ("edit", "correct", "propose_correction", "correct_metric"):
            with self.assertRaises(RuntimeError):
                getattr(adapter, name)()

    @unittest.skipUnless(HAS_BPY, "bpy 5.3.0 not installed")
    def test_blender_components_are_reported_per_island(self):
        with TemporaryDirectory() as d:
            blend = BlenderAdapterTests().make(Path(d) / "a.blend")
            raw = BlenderAdapter({}, "s", components=["BOX"]).raw(blend)
            self.assertEqual(len(raw["objects"]["BOX"]["components"]), 1)
            self.assertEqual(raw["objects"]["BOX"]["components"][0]["bbox_max"], [1.0, 2.0, 3.0])


class ContinuationTests(unittest.TestCase):
    def test_interval_metric_reuses_two_sided_contract(self):
        from blueprint_engine.contract import interval_metric
        m = interval_metric(1.0, 3.0, uncertainty=0.25)
        self.assertEqual((m["value"], m["tolerance"]), (2.0, 1.0))
        for x, expected in ((1.25, "PASS"), (2.75, "PASS"), (1.125, "HOLD"), (0.5, "OUTSIDE"),
                            (3.5, "OUTSIDE"), (0.875, "HOLD")):
            with self.subTest(x=x):
                self.assertEqual(metric_state(x - m["value"], m["tolerance"], 0.25), expected)
        for bad in ((1.0, float("inf")), (2.0, 1.0)):
            with self.assertRaises(ValueError):
                interval_metric(*bad)
        with self.assertRaises(ValueError):
            interval_metric(1.0, 1.4, uncertainty=0.25)      # PASS unreachable

    def test_official_crown_and_chin_are_subpixel_and_deterministic(self):
        from blueprint_engine.official_face import chin, crown
        with TemporaryDirectory() as d:
            path = Path(d) / "f.png"
            image = Image.new("RGBA", (20, 40), (0, 0, 0, 0))
            for x in range(20):
                image.putpixel((x, 5), (255, 255, 255, 128))
                for y in range(6, 40):
                    image.putpixel((x, y), (255, 230, 210, 255))
                image.putpixel((x, 30), (40, 20, 20, 255))
            image.save(path)
            c1, c2 = crown(path), crown(path)
            self.assertEqual(c1, c2)
            self.assertTrue(4.0 <= c1["y"] <= 6.0)
            self.assertAlmostEqual(chin(path, 10, (25, 35))["y"], 30.0)

    def test_compat_check_classifies_provenance_vs_design(self):
        from blueprint_engine.cases.compat_check import check
        with TemporaryDirectory() as d:
            src = png(Path(d) / "a.png")
            sha = file_sha256(src)
            for name, value, deps in (("old", 10.0, {"d": "2" * 64}), ("new", 10.0, {"d": "3" * 64}),
                                      ("moved", 11.0, {"d": "2" * 64})):
                t, r, _ = compile_target(image_blueprint(src, value), "g", registry(),
                                         native_sha256=sha, protected_baseline_sha256=sha,
                                         dependency_hashes=deps)
                root = Path(d) / name
                (root / "targets").mkdir(parents=True)
                (root / "handoff").mkdir()
                (root / "targets" / "g.json").write_text(json.dumps(dict(target=t, request=r)))
                (root / "handoff" / "g.json").write_text(json.dumps(handoff(t, r, [])))
            rep = check(Path(d) / "old", Path(d) / "new")["targets"]["targets/g.json"]
            self.assertEqual((rep["design_changed"], rep["provenance_changed"]),
                             ([], ["dependency_fingerprint"]))
            rep = check(Path(d) / "old", Path(d) / "moved")["targets"]["targets/g.json"]
            self.assertIn("values", rep["design_changed"])

    @unittest.skipUnless(HAS_BPY, "bpy 5.3.0 not installed")
    def test_gap_selector(self):
        with TemporaryDirectory() as d:
            blend = BlenderAdapterTests().make(Path(d) / "a.blend")
            adapter = BlenderAdapter({}, "s")
            value, u = adapter.value(adapter.raw(blend), ("gap", "BOX", "OTHER", 0))
            self.assertEqual(value, 4.0)                       # OTHER x 5..6, BOX x 0..1
            self.assertGreater(u, 0)


class EyelineTests(unittest.TestCase):
    def test_eyeline_extent_on_synthetic_stroke(self):
        from blueprint_engine.official_face import eyeline
        with TemporaryDirectory() as d:
            path = Path(d) / "e.png"
            image = Image.new("RGBA", (60, 30), (250, 220, 200, 255))     # skin
            for x in range(12, 44):
                image.putpixel((x, 10), (60, 25, 20, 255))                # warm dark stroke
                image.putpixel((x, 11), (60, 25, 20, 255))
            image.save(path)
            r = eyeline(path, (2, 2, 57, 20), 28)
            self.assertEqual((r["left"], r["right"], r["width"]), (12, 43, 32))
            self.assertEqual(r["ambiguous"], [])
            self.assertEqual(r["width_u"], 1.0)                           # sweep 0 + 2 x 0.5 px


class LowerBoundEngineTests(unittest.TestCase):
    def bp(self, src, bound="lower", tolerance=0.0, corrections=None):
        bp = Blueprint(blueprint_id="lb", asset_id="T", stage="s", status="TEST", canon_status="TEST")
        bp.add_source(register_source(src, source_id="img", role="OFFICIAL_CANON",
                                      projection="image-2d-uncalibrated", coordinate_system="px",
                                      units="px", provenance="t", license="t"))
        bp.add_element(element_id="w", kind="dimension", module="m", sources=["img"],
                       evidence=PROVISIONAL_DESIGN, coordinate_system="px", units="px", dims=1,
                       value=12.0, uncertainty=0.0)
        bp.add_group(target_id="g", measurement_id="alpha", coordinate_system="px", units="px",
                     projection="image-2d-uncalibrated", operation_id="m",
                     protection_scope_id="img.file", tolerance_basis="t", corrections=corrections,
                     intersection_limit=0 if corrections else None,
                     metrics={"x0": dict(element="w", value=8.0, tolerance=tolerance,
                                         uncertainty=0.0, evidence=PROVISIONAL_DESIGN,
                                         bound=bound)})
        return bp

    def test_invalid_bound_specifications_are_refused(self):
        with TemporaryDirectory() as d:
            src = png(Path(d) / "a.png")
            for kwargs in (dict(bound="upper"), dict(bound="both"), dict(tolerance=1.0),
                           dict(corrections={"x0": dict(operation_id="m", max_delta=1.0,
                                                        affects=["x0"], requires_pass=[])})):
                with self.subTest(**{k: str(v) for k, v in kwargs.items()}), \
                        self.assertRaises(BlueprintError):
                    self.bp(src, **kwargs)

    def test_lower_bound_compiles_and_is_refused_until_468_supports_it(self):
        from blueprint_engine.bounds import CONTRACT_SUPPORTS_LOWER_BOUND
        with TemporaryDirectory() as d:
            src = png(Path(d) / "a.png")
            sha = file_sha256(src)
            target, request, issues = compile_target(
                self.bp(src), "g", registry(), native_sha256=sha, protected_baseline_sha256=sha,
                dependency_hashes={"d": "2" * 64})
            self.assertEqual(target["lower_bound"], {"x0": 8.0})
            self.assertEqual(target["tolerances"]["x0"], 0.0)
            gate = handoff(target, request, issues)
            self.assertEqual(gate["factory_ready"], CONTRACT_SUPPORTS_LOWER_BOUND)
            if not CONTRACT_SUPPORTS_LOWER_BOUND:
                self.assertIn("contract_extension_required:lower_bound", gate["issues"])
            # measured x0 = 10 (alpha bbox) above L = 8: PASS, deficit 0
            obs = ImageAlphaAdapter({"x0": ("bbox", 0)}, "img.file").measure(src, target)
            row = evaluate(target, obs)["metrics"]["x0"]
            self.assertEqual((row["kind"], row["state"], row["deficit"], row["margin"]),
                             ("lower_bound", "PASS", 0.0, 2.0))

    def test_two_sided_targets_carry_no_lower_bound_field(self):
        with TemporaryDirectory() as d:
            src = png(Path(d) / "a.png")
            sha = file_sha256(src)
            target, _, _ = compile_target(image_blueprint(src), "g", registry(), native_sha256=sha,
                                          protected_baseline_sha256=sha,
                                          dependency_hashes={"d": "2" * 64})
            self.assertNotIn("lower_bound", target)

    def test_reference_matches_468_contract(self):
        """Parity: engine reference == #468 shared_blueprint_contract (patch applied at 2747ac90)."""
        import itertools
        import shared_blueprint_contract as c
        from blueprint_engine import bounds
        self.assertTrue(bounds.CONTRACT_SUPPORTS_LOWER_BOUND)
        self.assertIs(bounds.constrained_state, c.constrained_state)
        self.assertIs(bounds.deficit, c.deficit)
        self.assertIs(bounds.lower_bound_issues, c.lower_bound_issues)
        grid = (-.5, -.25, -.125, 0, .125, .25, .5)
        targets = [{"lower_bound": {"k": 1.0}, "tolerances": {"k": 0}, "values": {"k": 1.0}},
                   {"tolerances": {"k": .25}, "values": {"k": 1.0}}]
        R = bounds.REFERENCE
        for t in targets:
            for r, u in itertools.product(grid, (0, .125, .25)):
                self.assertEqual(c.constrained_state(t, "k", r, u),
                                 R["constrained_state"](t, "k", r, u))
                self.assertEqual(c.deficit(t, "k", r), R["deficit"](t, "k", r))
        bad = [{"lower_bound": {"k": float("nan")}, "tolerances": {"k": 0}, "values": {"k": 1.0}},
               {"lower_bound": {"k": 2.0}, "tolerances": {"k": 0}, "values": {"k": 1.0}},
               {"lower_bound": {"k": 1.0}, "tolerances": {"k": .1}, "values": {"k": 1.0}},
               {"lower_bound": {"k": 1.0}, "tolerances": {"k": 0}, "values": {"k": 1.0},
                "corrections": {"k": {}}},
               {"lower_bound": [], "tolerances": {"k": 0}, "values": {"k": 1.0}}]
        for t in bad:
            self.assertEqual(c.lower_bound_issues(t), R["lower_bound_issues"](t))
            self.assertTrue(c.lower_bound_issues(t))


class _StateAdapter:
    """Pure-Python Factory adapter over an in-memory state (no native file edits)."""

    def __init__(self, state, u, response):
        from blueprint_engine.measure import _Adapter
        self.inner = type("A", (_Adapter,), dict(
            raw=lambda s, native, deadline=None: dict(self.state),
            value=lambda s, raw, key: (raw[key], self.u),
            protected=lambda s, native, raw: "a" * 64))({k: k for k in state}, "scope")
        self.state, self.u, self.response = dict(state), u, response

    def measure(self, native, target, *, deadline=None):
        return self.inner.measure(native, target)

    reopen = measure

    def finish(self, native, target, *, deadline=None):
        return dict(self.inner.evidence_files)

    def edit(self, native, target, *, deadline=None):
        return None

    def propose_correction(self, native, target, obs, key, *, deadline=None):
        return -obs["residuals"][key]

    def correct_metric(self, native, target, key, amount, *, deadline=None):
        self.state[key] += amount
        for other, delta in self.response.items():
            self.state[other] += delta
        Path(native).write_bytes(Path(native).read_bytes() + b"x")   # emulate a saved edit
        return amount


class AcceptanceQATests(unittest.TestCase):
    """Final QA items requested by independent design QA (#485 comment 7100440033)."""

    def target(self, src, *, b_value=5.0, c_lower=2.0, affects=("a",), b_u=0.0):
        bp = Blueprint(blueprint_id="t", asset_id="T", stage="s", status="TEST",
                       canon_status="TEST")
        bp.add_source(register_source(src, source_id="img", role="NATIVE_WORKING",
                                      projection="data", coordinate_system="c", units="u",
                                      provenance="t", license="t"))
        for e in "abc":
            bp.add_element(element_id=e, kind="dimension", module="m", sources=["img"],
                           evidence=PROVISIONAL_DESIGN, coordinate_system="c", units="u",
                           dims=0, value=1.0, uncertainty=0.0)
        bp.add_group(target_id="g", measurement_id="m", coordinate_system="c", units="u",
                     projection="data", operation_id="m", protection_scope_id="scope",
                     tolerance_basis="t", intersection_limit=0,
                     corrections={"a": dict(operation_id="m", max_delta=1.0,
                                            affects=list(affects), requires_pass=["c"])},
                     metrics={"a": dict(element="a", value=10.0, tolerance=.1, uncertainty=0.0,
                                        evidence=PROVISIONAL_DESIGN),
                              "b": dict(element="b", value=b_value, tolerance=.1,
                                        uncertainty=b_u, evidence=PROVISIONAL_DESIGN),
                              "c": dict(element="c", value=c_lower, tolerance=0.0,
                                        uncertainty=0.0, evidence=PROVISIONAL_DESIGN,
                                        bound="lower")})
        sha = file_sha256(src)
        target, request, issues = compile_target(bp, "g", registry(), native_sha256=sha,
                                                 protected_baseline_sha256="a" * 64,
                                                 dependency_hashes={"d": "2" * 64})
        gate = handoff(target, request, issues)
        self.assertTrue(gate["factory_ready"], gate)
        return target, request

    def run_factory(self, state, u, response, **kw):
        with TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src.bin"
            src.write_bytes(b"native")
            target, request = self.target(src, **kw)
            adapter = _StateAdapter(state, u, response)
            stage = dict(id="s", fingerprint="f")
            (root / "f").mkdir()
            try:
                return execute_factory_stage(root / "f", src, stage, target, request, adapter,
                                             time.monotonic() + 60, lambda: None), None
            except Exception as exc:              # noqa: BLE001
                self.assertEqual(src.read_bytes(), b"native")     # source never touched
                self.assertTrue(list((root / "f" / "quarantine").glob("factory-*")))
                return None, exc

    def test_clean_correction_passes(self):
        cp, exc = self.run_factory(dict(a=10.5, b=5.0, c=2.5), .01, {})
        self.assertIsNone(exc)
        self.assertEqual(cp["observation"]["actual"]["a"], 10.0)

    def test_hold_to_outside_on_other_metric_stops(self):
        # b: |r| .11, u .02 -> HOLD; correction moves b by .03 (<= .04 noise) -> OUTSIDE
        cp, exc = self.run_factory(dict(a=10.5, b=5.11, c=2.5), .02, {"b": .03})
        self.assertIsNone(cp)
        self.assertIn("interfered with metric: b", str(exc))

    def test_hold_on_affected_metric_blocks_correction_and_remeasures_once(self):
        cp, exc = self.run_factory(dict(a=10.5, b=5.11, c=2.5), .02, {}, affects=("a", "b"))
        self.assertIsNone(cp)
        self.assertIn("factory measurement blocked", str(exc))

    def test_lower_bound_crossing_by_other_correction_stops(self):
        # c: r = +.01 PASS (u .002+.002); correction moves c by -.009 -> not PASS
        cp, exc = self.run_factory(dict(a=10.5, b=5.0, c=2.01), .002, {"c": -.009})
        self.assertIsNone(cp)
        self.assertIn("interfered with metric: c", str(exc))

    def test_lower_bound_metric_cannot_be_auto_corrected(self):
        with TemporaryDirectory() as d:
            src = Path(d) / "s"
            src.write_bytes(b"n")
            bp = Blueprint(blueprint_id="t", asset_id="T", stage="s", status="T", canon_status="T")
            bp.add_source(register_source(src, source_id="img", role="NATIVE_WORKING",
                                          projection="data", coordinate_system="c", units="u",
                                          provenance="t", license="t"))
            bp.add_element(element_id="c", kind="dimension", module="m", sources=["img"],
                           evidence=PROVISIONAL_DESIGN, coordinate_system="c", units="u",
                           dims=0, value=1.0, uncertainty=0.0)
            with self.assertRaises(BlueprintError):
                bp.add_group(target_id="g", measurement_id="m", coordinate_system="c",
                             units="u", projection="data", operation_id="m",
                             protection_scope_id="s", tolerance_basis="t", intersection_limit=0,
                             corrections={"c": dict(operation_id="m", max_delta=1.0,
                                                    affects=["c"], requires_pass=[])},
                             metrics={"c": dict(element="c", value=1.0, tolerance=0.0,
                                                uncertainty=0.0, evidence=PROVISIONAL_DESIGN,
                                                bound="lower")})

    def test_malformed_and_nonfinite_inputs_are_refused(self):
        with TemporaryDirectory() as d:
            src = Path(d) / "s"
            src.write_bytes(b"n")
            for field, bad in (("value", float("nan")), ("value", float("inf")),
                               ("tolerance", -1.0), ("tolerance", float("inf")),
                               ("uncertainty", float("nan")), ("uncertainty", -0.1),
                               ("value", "1.0"), ("value", True)):
                with self.subTest(field=field, bad=bad):
                    metric = dict(element="c", value=1.0, tolerance=0.1, uncertainty=0.0,
                                  evidence=PROVISIONAL_DESIGN)
                    metric[field] = bad
                    bp = Blueprint(blueprint_id="t", asset_id="T", stage="s", status="T",
                                   canon_status="T")
                    bp.add_source(register_source(src, source_id="img", role="NATIVE_WORKING",
                                                  projection="data", coordinate_system="c",
                                                  units="u", provenance="t", license="t"))
                    bp.add_element(element_id="c", kind="dimension", module="m",
                                   sources=["img"], evidence=PROVISIONAL_DESIGN,
                                   coordinate_system="c", units="u", dims=0, value=1.0,
                                   uncertainty=0.0)
                    with self.assertRaises(BlueprintError):
                        bp.add_group(target_id="g", measurement_id="m", coordinate_system="c",
                                     units="u", projection="data", operation_id="m",
                                     protection_scope_id="s", tolerance_basis="t",
                                     metrics={"c": metric})
            # tampered compiled targets and non-finite observations fail closed
            target, request = self.target(src)
            for mutate in (lambda t: t["lower_bound"].update(c=float("nan")),
                           lambda t: t["lower_bound"].update(c=3.0),
                           lambda t: t["tolerances"].update(c=0.5),
                           lambda t: t.update(lower_bound=[]),
                           lambda t: t["uncertainty"].update(a=float("inf"))):
                t = copy.deepcopy(target)
                mutate(t)
                try:                                 # refusal or exception: both fail closed
                    ready = handoff(t, request, [])["factory_ready"]
                except ValueError:
                    ready = False
                self.assertFalse(ready)
            obs = _StateAdapter(dict(a=10.0, b=5.0, c=2.5), 0.0, {}).measure(src, target)
            for key, bad in (("a", float("nan")), ("c", float("inf")), ("b", -1.0)):
                o = copy.deepcopy(obs)
                o["uncertainty"][key] = bad
                self.assertTrue(measurement_issues(target, request, o), (key, bad))


class ReuseTests(unittest.TestCase):
    """Character and map cases share one engine path; no case forks the judgement."""
    FORBIDDEN = {"metric_state", "constrained_state", "deficit", "evaluate", "compile_target",
                 "handoff", "target_issues", "measurement_issues"}

    def test_cases_reuse_engine_core_without_redefinition(self):
        import ast
        cases = Path(__file__).resolve().parents[1] / "cases"
        uses = {}
        for path in sorted(cases.glob("*.py")):
            tree = ast.parse(path.read_text())
            defined = {n.name for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            self.assertFalse(defined & self.FORBIDDEN, path.name)
            uses[path.stem] = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                               for a in n.names}
        character = ("morwen_layer0", "morwen_face_vrm")
        world = ("lind_home", "lind_home_porch", "native_correction_loop")
        for name in character + world:
            self.assertTrue({"run_group", "compile_target", "evaluate"} & uses[name], name)
            self.assertIn("Blueprint", uses[name], name)


class SharedTransportGuardTests(unittest.TestCase):
    def test_shared_transport_refuses_production_keys(self):
        from blueprint_engine.cases import native_correction_loop as loop
        for key in (None, "", *sorted(loop.PRODUCTION_KEYS)):
            with self.subTest(key=key), self.assertRaises(SystemExit):
                loop.run("/nonexistent", "/nonexistent", transport="/tmp/x.git", lease_asset=key)
