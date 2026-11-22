from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from shared_blueprint_contract import digest_record, measurement_issues, target_issues
from shared_session_controller import run
from session_plan import sha


class BlueprintContractTests(unittest.TestCase):
    def setUp(self):
        self.req = dict(target_id="edge", source_sha256="a"*64,
                        reference_sha256="b"*64, dependency_hashes={"frame": "c"*64})
        self.target = dict(
            target_id="edge", source_sha256="a"*64, sha256="b"*64,
            coordinate_system="frame-local", units="m", projection="native-3d",
            measurement_id="edge-span", values={"span": 1.0},
            tolerances={"span": .02}, uncertainty={"span": .003},
            operation={"id": "align", "qualified": True, "evidence_sha256": "d"*64},
            protection={"scope_id": "frame", "baseline_sha256": "e"*64},
            dependency_fingerprint=digest_record(self.req["dependency_hashes"]),
        )
        self.observation = {key: self.target[key] for key in
                            ("target_id", "source_sha256", "coordinate_system", "units",
                             "projection", "measurement_id", "dependency_fingerprint")}
        self.observation.update(
            operation_id="align", native_sha256="f"*64, evidence_sha256="0"*64,
            protected_scope_id="frame", protected_sha256="e"*64,
            actual={"span": 1.01}, residuals={"span": .01}, uncertainty={"span": .004},
            target_contract_sha256=digest_record(self.target),
        )

    def test_accepts_matched_native_measurement_and_conservative_residual(self):
        self.assertEqual(target_issues(self.target, self.req), [])
        self.assertEqual(measurement_issues(self.target, self.req, self.observation), [])

    def test_rejects_wrong_coordinate_context_and_stale_dependencies(self):
        for key, value in (("projection", "perspective"), ("units", "cm"),
                           ("dependency_fingerprint", "0"*64)):
            with self.subTest(key=key):
                self.assertEqual(measurement_issues(self.target, self.req,
                                                    {**self.observation, key: value}),
                                 ["observation_context"])

    def test_unknown_tolerance_uncertainty_or_operation_blocks_target(self):
        for key, value, issue in (
            ("tolerances", {}, "design_tolerances"),
            ("uncertainty", {"span": float("nan")}, "design_uncertainty"),
            ("operation", {**self.target["operation"], "qualified": False}, "operation_qualification"),
        ):
            with self.subTest(key=key):
                target = deepcopy(self.target)
                target[key] = value
                self.assertIn(issue, target_issues(target, self.req))

    def test_rejects_regressed_protection_forged_residual_and_uncertain_measurement(self):
        for change, issue in (
            ({"protected_sha256": "0"*64}, "protected_scope"),
            ({"residuals": {"span": 0}}, "residual:span"),
            ({"uncertainty": {"span": .009}}, "tolerance:span"),
        ):
            with self.subTest(issue=issue):
                self.assertIn(issue, measurement_issues(self.target, self.req,
                                                        {**self.observation, **change}))

    def test_worker_blocks_mismatched_measurement_before_publication(self):
        commit = "1"*40
        request = {**self.req, "asset_id": "LIND-HOME", "head_sha": commit, "stage": "edit"}
        stage = dict(id="edit", deps=[], qualified=True, seconds=2, fingerprint="fixture")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            native = root / "result"
            native.write_text("stage output")
            result = dict(path=native.name, sha256=sha(native), reopened=True,
                          fingerprint="fixture", observation=self.observation)
            persist = Mock()
            with patch("shared_session_controller.acquire", return_value="2"*40), patch(
                "shared_session_controller.assert_owned"
            ):
                with self.assertRaisesRegex(RuntimeError, "checkpoint blocked: native_sha256"):
                    run("isolated", "LIND-HOME", commit, root, [stage], {}, lambda *args: result,
                        persist, budget=10, reserve=2,
                        blueprint_targets={"edit": (self.target, request)})
            persist.assert_not_called()


if __name__ == "__main__":
    unittest.main()
