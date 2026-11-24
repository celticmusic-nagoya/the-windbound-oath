"""One-sided lower-bound metrics (#468 contract extension proposed from #485).

Two-sided targets keep their behaviour and contract SHA; lower-bound metrics use
r = x - L: r - u >= 0 PASS, r + u < 0 OUTSIDE, otherwise HOLD. Movement further
above the bound is never a worsening; lower-bound metrics are not auto-corrected.
"""
from copy import deepcopy
import itertools
import json
import unittest

from shared_blueprint_contract import (constrained_state, deficit, digest_record,
                                       measurement_issues, metric_state, target_issues)
import test_shared_blueprint_contract as contract_fixture
import test_shared_item_correction as factory_fixture


class LowerBoundContractTests(contract_fixture.BlueprintContractTests):
    def bounded(self, lower=1.0):
        target = deepcopy(self.target)
        target["values"]["clearance"] = lower
        target["tolerances"]["clearance"] = 0
        target["uncertainty"]["clearance"] = .001
        target["lower_bound"] = {"clearance": lower}
        return target

    def observe(self, target, x, u=.002):
        obs = deepcopy(self.observation)
        obs["actual"]["clearance"] = x
        obs["residuals"]["clearance"] = x - target["values"]["clearance"]
        obs["uncertainty"]["clearance"] = u
        obs["target_contract_sha256"] = digest_record(target)
        return obs

    def test_boundaries(self):
        t = {"lower_bound": {"k": 1.0}, "tolerances": {"k": 0}}
        for r, u, state in ((0, 0, "PASS"), (.25, .25, "PASS"), (10, .5, "PASS"),
                            (.125, .25, "HOLD"), (-.25, .25, "HOLD"), (-.375, .25, "OUTSIDE")):
            with self.subTest(r=r, u=u):
                self.assertEqual(constrained_state(t, "k", r, u), state)

    def test_two_sided_behaviour_and_contract_sha_unchanged(self):
        before = digest_record(self.target)
        self.assertEqual(target_issues(self.target, self.req), [])
        self.assertEqual(digest_record(self.target), before)
        self.assertNotIn("lower_bound", self.target)
        grid = (-.5, -.25, 0, .125, .25, .5)
        for r, t, u in itertools.product(grid, (0, .25, .5), (0, .125, .25)):
            self.assertEqual(constrained_state({"tolerances": {"k": t}}, "k", r, u),
                             metric_state(r, t, u))

    def test_valid_bound_accepts_values_above_lower_bound(self):
        target = self.bounded()
        self.assertEqual(target_issues(target, self.req), [])
        self.assertEqual(measurement_issues(target, self.req, self.observe(target, 1.66)), [])
        # u = .001 (target) + .002 (observation): PASS needs x - 1.0 >= .003
        self.assertEqual(measurement_issues(target, self.req, self.observe(target, 1.004)), [])
        self.assertIn("tolerance:clearance",                       # HOLD
                      measurement_issues(target, self.req, self.observe(target, 1.002)))
        self.assertIn("tolerance:clearance",
                      measurement_issues(target, self.req, self.observe(target, 0.9)))

    def test_invalid_bound_specifications_are_rejected(self):
        cases = []
        for mutate in (lambda t: t.update(lower_bound=[]),
                       lambda t: t.update(lower_bound={}),
                       lambda t: t["lower_bound"].update(missing=1.0),
                       lambda t: t["lower_bound"].update(clearance=1.5),
                       lambda t: t["lower_bound"].update(clearance=float("inf")),
                       lambda t: t["tolerances"].update(clearance=.1),
                       lambda t: t.update(corrections={"clearance": {}}, intersection_limit=0)):
            target = self.bounded()
            mutate(target)
            cases.append(target)
        for target in cases:
            with self.subTest(target=json.dumps(target.get("lower_bound"), default=str)):
                self.assertTrue([i for i in target_issues(target, self.req)
                                 if i.startswith(("lower_bound", "correction"))])

    def test_deficit_ignores_movement_above_bound(self):
        target = self.bounded()
        self.assertEqual(deficit(target, "clearance", .66), 0)
        self.assertEqual(deficit(target, "clearance", -.2), .2)
        self.assertEqual(deficit(target, "span", -.2), .2)


class LowerBoundFactoryTests(factory_fixture.ItemCorrectionTests):
    def setUp(self):
        super().setUp()
        values = json.loads(self.source.read_text())
        values["clearance"] = 1.66
        self.source.write_text(json.dumps(values))
        from session_plan import sha
        self.request["source_sha256"] = self.target["source_sha256"] = sha(self.source)
        self.target["values"]["clearance"] = 1.0
        self.target["tolerances"]["clearance"] = 0
        self.target["uncertainty"]["clearance"] = 0
        self.target["lower_bound"] = {"clearance": 1.0}
        self.target["corrections"]["length"]["affects"].append("clearance")
        self.clearance_step = .1
        self.width_fixed = True

    def measure(self, native, target, *, deadline):
        observed = super().measure(native, target, deadline=deadline)
        observed["uncertainty"]["clearance"] = .001
        observed["uncertainty"]["width"] = .005
        return observed

    reopen = measure

    def correct_metric(self, native, target, key, amount, *, deadline):
        applied = super().correct_metric(native, target, key, amount, deadline=deadline)
        values = json.loads(native.read_text())
        values["clearance"] += self.clearance_step
        native.write_text(json.dumps(values))
        return applied

    def test_increase_above_lower_bound_is_not_interference(self):
        checkpoint = self.execute()
        self.assertTrue(checkpoint["reopened"])
        self.assertIn("length", self.calls)

    def test_drop_below_lower_bound_is_interference(self):
        self.clearance_step = -.7
        with self.assertRaisesRegex(RuntimeError, "interfered with metric: clearance"):
            self.execute()

    def test_lower_bound_outside_is_not_auto_corrected(self):
        del self.target["corrections"]
        del self.target["intersection_limit"]
        values = json.loads(self.source.read_text())
        values.update(length=1.0, clearance=.5)
        self.source.write_text(json.dumps(values))
        from session_plan import sha
        self.request["source_sha256"] = self.target["source_sha256"] = sha(self.source)
        self.correct = lambda *a, **k: self.calls.append("unrestricted-correct")
        with self.assertRaisesRegex(RuntimeError, "tolerance:clearance"):
            self.execute()
        self.assertNotIn("unrestricted-correct", self.calls)


# Inherited fixture tests run again under the lower-bound fixtures; keep only new ones.
for name in [n for n in dir(LowerBoundContractTests) if n.startswith("test_")
             and n not in LowerBoundContractTests.__dict__]:
    setattr(LowerBoundContractTests, name, None)
for name in [n for n in dir(LowerBoundFactoryTests) if n.startswith("test_")
             and n not in LowerBoundFactoryTests.__dict__]:
    setattr(LowerBoundFactoryTests, name, None)


if __name__ == "__main__":
    unittest.main()
