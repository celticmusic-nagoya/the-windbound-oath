"""Offline AI3D synthetic canary gates; no GPU, network, weights, or protected art."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "asset_pipeline" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

gate = load("ai3d_pilot_preflight", "ai3d_pilot_preflight.py")
generator = load("create_ai3d_synthetic_canary", "create_ai3d_synthetic_canary.py")

class TestOfflineCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.image = Path(self.tmp.name) / "canary.png"
        self.image.write_bytes(generator.make_png())

    def test_png_is_deterministic_rgba(self):
        data = self.image.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(data[24:26], b"\x08\x06")
        self.assertEqual(data, generator.make_png())

    def test_owned_synthetic_canary_admitted_only_as_input(self):
        result = gate.assess(self.image, model="TripoSR",
                             source_class="project-generated-synthetic-canary",
                             external_upload=False)
        self.assertEqual(result["status"], "PASS_INPUT_ONLY_NOT_MODEL_EXECUTION")
        self.assertEqual(result["gpu_inference"], "NOT_RUN")
        self.assertEqual(result["G1"], "BLOCKED")
        self.assertEqual(result["G3"], "NOT_RUN")

    def test_alternate_open_model_not_execution(self):
        result = gate.assess(self.image, model="InstantMesh",
                             source_class="project-generated-synthetic-canary",
                             external_upload=False)
        self.assertEqual(result["status"], "PASS_INPUT_ONLY_NOT_MODEL_EXECUTION")

    def test_blocks_cloud_transfer(self):
        result = gate.assess(self.image, model="TripoSR",
                             source_class="project-generated-synthetic-canary",
                             external_upload=True)
        self.assertEqual(result["status"], "BLOCKED")

    def test_blocks_unverified_provenance(self):
        result = gate.assess(self.image, model="TripoSR", source_class="official-character",
                             external_upload=False)
        self.assertEqual(result["status"], "BLOCKED")

    def test_blocks_unlisted_provider(self):
        result = gate.assess(self.image, model="unreviewed-service",
                             source_class="project-generated-synthetic-canary",
                             external_upload=False)
        self.assertEqual(result["status"], "BLOCKED")

    def test_blocks_hash_mismatch_and_missing_input(self):
        result = gate.assess(self.image, model="TripoSR",
                             source_class="project-generated-synthetic-canary",
                             external_upload=False, expected_sha256="0" * 64)
        self.assertEqual(result["status"], "BLOCKED")
        result = gate.assess(self.image.with_name("absent.png"), model="TripoSR",
                             source_class="project-generated-synthetic-canary",
                             external_upload=False)
        self.assertEqual(result["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
