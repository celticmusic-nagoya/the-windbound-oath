import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from session_plan import sha
from shared_asset_lease import git
from shared_blueprint_contract import digest_record, metric_state
from shared_factory_stage import execute_factory_stage
from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint
from shared_session_controller import run


class ItemCorrectionTests(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.source = self.root / "source.blend"
        self.source.write_text(json.dumps({"length": 1.5, "width": 1.19}))
        source = sha(self.source)
        dep = {"base": "b"*64}
        self.target = dict(
            sha256="a"*64, target_id="lock", source_sha256=source,
            coordinate_system="head-local", units="m", projection="native-3d", measurement_id="section",
            values={"length": 1.0, "width": 1.0}, tolerances={"length": .2, "width": .2},
            uncertainty={"length": 0, "width": 0}, intersection_limit=1,
            operation=dict(id="observe", qualified=True, evidence_sha256="c"*64),
            protection=dict(scope_id="scalp", baseline_sha256="d"*64),
            dependency_fingerprint=digest_record(dep),
            corrections={"length": dict(operation_id="adjust-length", evidence_sha256="e"*64,
                                       max_delta=.6, affects=["length"], requires_pass=[])},
        )
        self.stage = dict(id="lock", qualified=True, deps=[], seconds=5, fingerprint="fixture")
        self.request = dict(target_id="lock", asset_id="MORWEN", stage="lock",
                            source_sha256=source, reference_sha256="a"*64, dependency_hashes=dep)
        self.calls = []
        self.protected = "d"*64
        self.remeasure_width = False
        self.interfere = False
        self.fail_correction = False
        self.intersections = 0
        self.changed_dependency = False
        self.introduce_intersection = False

    def edit(self, native, target, *, deadline):
        pass

    def measure(self, native, target, *, deadline):
        data = json.loads(native.read_text())
        self.calls.append("measure")
        width_uncertainty = .03
        if self.remeasure_width and self.calls.count("measure") >= 3:
            width_uncertainty = .005
        observed = {
            **{key: target[key] for key in ("target_id", "source_sha256", "coordinate_system",
                                           "units", "projection", "measurement_id", "dependency_fingerprint")},
            "operation_id": target["operation"]["id"], "target_contract_sha256": digest_record(target),
            "actual": data, "residuals": {key: value-1 for key,value in data.items()},
            "uncertainty": {"length": .01, "width": width_uncertainty},
            "native_sha256": sha(native), "evidence_sha256": "f"*64,
            "protected_scope_id": "scalp", "protected_sha256": self.protected,
            "intersections": self.intersections,
        }
        if self.changed_dependency:
            observed["dependency_fingerprint"] = "0"*64
        return observed

    def propose_correction(self, native, target, observed, key, *, deadline):
        return -.5

    def correct_metric(self, native, target, key, amount, *, deadline):
        self.calls.append(key)
        if self.fail_correction:
            raise RuntimeError("injected correction failure")
        values = json.loads(native.read_text())
        values[key] += amount
        if self.interfere:
            values["width"] += .1
        if self.introduce_intersection:
            self.intersections += 1
        native.write_text(json.dumps(values))
        return amount

    def finish(self, native, target, *, deadline):
        self.calls.append("finish")

    reopen = measure

    def execute(self):
        return execute_factory_stage(self.root, self.source, self.stage, self.target,
                                     self.request, self, time.monotonic()+10, lambda: None)

    def journal(self):
        return json.loads(next((self.root / "quarantine").glob("*/correction-journal.json")).read_text())

    def test_residual_boundaries(self):
        self.assertEqual(metric_state(3, 5, 2), "PASS")
        self.assertEqual(metric_state(7, 5, 2), "HOLD")
        self.assertEqual(metric_state(8, 5, 2), "OUTSIDE")

    def test_independent_outside_is_corrected_but_ambiguous_stage_is_not_published(self):
        with self.assertRaisesRegex(RuntimeError, "tolerance:width"):
            self.execute()
        self.assertEqual(self.calls, ["measure", "length", "measure", "measure"])
        journal = self.journal()
        self.assertEqual(journal["status"], "BLOCKED")
        operation = journal["events"][1]
        self.assertEqual(operation["applied_delta"], -.5)
        self.assertEqual(operation["response"]["length"], -.5)

    def test_cross_dependency_stops_before_correction(self):
        self.target["corrections"]["length"]["affects"].append("width")
        with self.assertRaisesRegex(RuntimeError, "tolerance:"):
            self.execute()
        self.assertNotIn("length", self.calls)
        self.assertEqual(self.journal()["events"][-1]["blocked"]["length"], "interference_or_dependency")

    def test_protection_and_dependency_mismatch_never_reach_correction(self):
        self.protected = "0"*64
        with self.assertRaisesRegex(RuntimeError, "protected_scope"):
            self.execute()
        self.assertNotIn("length", self.calls)
        self.protected = "d"*64
        self.changed_dependency = True
        with self.assertRaisesRegex(RuntimeError, "observation_context"):
            self.execute()
        self.assertNotIn("length", self.calls)

    def test_intersection_regression_is_blocked_even_within_limit(self):
        self.introduce_intersection = True
        with self.assertRaisesRegex(RuntimeError, "increased intersections"):
            self.execute()
        self.assertEqual(self.journal()["status"], "BLOCKED")

    def test_correction_interference_quarantines(self):
        self.interfere = True
        with self.assertRaisesRegex(RuntimeError, "interfered with metric: width"):
            self.execute()
        self.assertEqual(self.journal()["status"], "BLOCKED")

    def test_correction_exception_preserves_evidence_and_source(self):
        self.fail_correction = True
        with self.assertRaisesRegex(RuntimeError, "injected correction"):
            self.execute()
        self.assertEqual(self.journal()["events"][1]["requested_delta"], -.5)
        self.assertEqual(sha(self.source), self.request["source_sha256"])

    def test_success_journal_restores_with_checkpoint_without_repeating_edit(self):
        previous = Path.cwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(self.root)
        git("init", "-q")
        git("config", "user.email", "qa@invalid")
        git("config", "user.name", "Test")
        git("commit", "--allow-empty", "-qm", "fixture")
        head = git("rev-parse", "HEAD")
        remote = str(self.root/"remote.git")
        git("init", "--bare", "-q", remote)
        self.request["head_sha"] = head
        self.remeasure_width = True
        ledger = {}
        store = GitCheckpointStore(remote, "MORWEN", self.root)
        kwargs = dict(fenced=True, budget=20, reserve=2,
                      blueprint_targets={"lock": (self.target, self.request)},
                      factory_stages={"lock": (self.source, self)})
        self.assertEqual(run(remote, "MORWEN", head, self.root, [self.stage], ledger, None, store, **kwargs),
                         ["lock"])
        restored = self.root/"restored"
        records = restore_checkpoint(remote, "MORWEN", store.previous, restored, time.monotonic()+10)
        journal_name = next(iter(records["lock"]["files"]))
        self.assertEqual(json.loads((restored/journal_name).read_text())["status"], "PASS")
        restored_store = GitCheckpointStore(remote, "MORWEN", restored, previous=store.previous)
        self.calls.clear()
        self.assertEqual(run(remote, "MORWEN", head, restored, [self.stage], records, None,
                             restored_store, **kwargs), [])
        self.assertEqual(self.calls, [])
