from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from asset_library_eligibility import assess_reuse
from session_plan import sha


class LibraryEligibilityTests(unittest.TestCase):
    def test_requires_current_licensed_bytes_and_dependencies(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mesh").write_text("fixture")
            (root / "license").write_text("fixture evidence")
            files = {name: sha(root / name) for name in ("mesh", "license")}
            entry = dict(dependency_fingerprint="a"*64, native_path="mesh",
                         manifest=dict(files=files, output_contract="mesh"),
                         license=dict(id="fixture", reviewed=True, permitted_uses=["preview"],
                                      evidence_path="license", evidence_sha256=files["license"]))
            def decide(usage="preview", dependency="a"*64):
                return assess_reuse(root, entry, usage=usage, dependency_fingerprint=dependency,
                                    output_contract="mesh")["decision"]
            self.assertEqual(decide(), "REUSE_ELIGIBLE")
            self.assertEqual(decide(usage="redistribution"), "BLOCKED_LICENSE")
            self.assertEqual(decide(dependency="b"*64), "BLOCKED_DEPENDENCIES")
            (root / "license").write_text("changed after review")
            self.assertEqual(decide(), "BLOCKED_ASSET_BYTES")
