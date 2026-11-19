#!/usr/bin/env python3
"""Unit tests for the candidate Rilde semantic topology contract (stdlib only)."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/map_blender/validate_lind_new_world_topology.py"
GRAPH = ROOT / "docs/production/lind-new-world-topology.v1.json"
spec = importlib.util.spec_from_file_location("lind_topology_validator", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestLindTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    def test_baseline(self):
        self.assertEqual(module.validate(self.graph), [])

    def test_source_sha_mutation_rejected(self):
        data = copy.deepcopy(self.graph)
        data["source"]["sha256"] = "0" * 64
        self.assertTrue(module.validate(data))

    def test_missing_cliff_rejected(self):
        data = copy.deepcopy(self.graph)
        data["nodes"] = [n for n in data["nodes"] if n["id"] != "windward_cliffs_wnw"]
        self.assertTrue(module.validate(data))

    def test_raid_jump_reversed_rejected(self):
        data = copy.deepcopy(self.graph)
        jump = next(e for e in data["edges"] if e["kind"] == "story_jump")
        jump["from"], jump["to"] = jump["to"], jump["from"]
        self.assertTrue(module.validate(data))

    def test_raid_jump_walkable_rejected(self):
        data = copy.deepcopy(self.graph)
        jump = next(e for e in data["edges"] if e["kind"] == "story_jump")
        jump["kind"] = "walk"
        self.assertTrue(module.validate(data))

    def test_unapproved_metric_rejected(self):
        data = copy.deepcopy(self.graph)
        data["metric"]["meters_per_unit"] = 1.0
        self.assertTrue(module.validate(data))

    def test_dangling_edge_rejected(self):
        data = copy.deepcopy(self.graph)
        data["edges"][0]["to"] = "unknown"
        self.assertTrue(module.validate(data))

    def test_duplicate_node_rejected(self):
        data = copy.deepcopy(self.graph)
        data["nodes"].append(copy.deepcopy(data["nodes"][0]))
        self.assertTrue(module.validate(data))


if __name__ == "__main__":
    unittest.main()
