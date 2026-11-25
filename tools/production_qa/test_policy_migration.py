import json
from pathlib import Path
import shutil
import tempfile
import unittest

from shared_production_readiness import policy_authority, policy_migration_issues


ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "docs/policy"


class PolicyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((POLICY_DIR / "POLICY_REGISTRY.json").read_text())
        self.sources = json.loads((POLICY_DIR / "PRODUCTION_FIRST_V5_SOURCES.json").read_text())

    def test_all_current_sources_match(self):
        self.assertEqual(policy_migration_issues(ROOT, self.registry, self.sources), [])

    def test_only_exact_active_paths_can_supply_authority(self):
        reference = next(iter(self.sources))
        self.assertEqual(policy_authority(self.registry, reference), "ACTIVE")
        self.assertEqual(policy_authority(self.registry, "./" + reference), "REFERENCE_ONLY")
        self.assertEqual(policy_authority(self.registry, "unregistered.md"), "REFERENCE_ONLY")
        for historical in self.registry["superseded"]:
            self.assertEqual(policy_authority(self.registry, historical), "HISTORICAL")

    def test_early_retirement_is_rejected(self):
        self.registry["active"].remove(next(iter(self.sources)))
        self.assertEqual(policy_migration_issues(ROOT, self.registry, self.sources),
                         ["migration inventory"])

    def test_historical_status_wins_on_registry_conflict(self):
        reference = next(iter(self.sources))
        self.registry["superseded"].append(reference)
        self.assertEqual(policy_migration_issues(ROOT, self.registry, self.sources),
                         [f"authority conflict: {reference}"])

    def test_a_deleted_condition_changes_source_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(POLICY_DIR, root / "docs/policy")
            reference = next(iter(self.sources))
            path = root / reference
            path.write_bytes(path.read_bytes().split(b"\n", 2)[-1])
            self.assertEqual(policy_migration_issues(root, self.registry, self.sources),
                             [f"source changed: {reference}"])
