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
