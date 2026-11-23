import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from session_plan import sha
from studio_checkpoint_export import export_records


class StudioCheckpointExportTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.native = self.root / "source.blend"
        self.native.write_bytes(b"private native")
        self.preview = self.root / "preview.png"
        self.preview.write_bytes(b"approved preview fixture")
        self.descriptor = self.root / "studio.json"
        self.data = dict(checkpoint_path=self.preview.name, path="previews/front.png",
                         sha256=sha(self.preview), head="a"*40, run_id=8, artifact_id=9,
                         artifact_sha256="b"*64, expires_at="2027-02-20T16:09:36Z",
                         stage="isolated candidate",
                         qa={"G1": "NOT_RUN", "G2": "NOT_RUN", "G3": "PASS", "G4": "NOT_RUN"},
                         adoption="CANDIDATE")
        self.approval = dict(checkpoint_stage="preview", descriptor_path=self.descriptor.name,
                             public=True, redistribution_verified=True, review_ref="studio-review")
        self.ledger = {"preview": dict(path=self.native.name, sha256=sha(self.native), reopened=True,
                                       files={self.preview.name: sha(self.preview)})}
        self.save_descriptor()

    def save_descriptor(self):
        self.descriptor.write_text(json.dumps(self.data))
        self.approval["descriptor_sha256"] = sha(self.descriptor)
        self.ledger["preview"]["files"][self.descriptor.name] = sha(self.descriptor)

    def export(self):
        return export_records(self.root, self.ledger, [self.approval])

    def test_exports_bound_metadata_preserving_candidate_and_unrun_gates(self):
        self.assertEqual(self.export(), [{k:v for k,v in self.data.items() if k!="checkpoint_path"}])
        self.assertEqual(export_records(self.root, self.ledger, []), [])

    def test_rejects_missing_authority_and_changed_bytes(self):
        self.approval["redistribution_verified"] = False
        with self.assertRaisesRegex(ValueError, "approval"):
            self.export()
        self.approval["redistribution_verified"] = True
        self.preview.write_bytes(b"different")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.export()

    def test_rejects_native_and_noncanonical_archive_paths(self):
        self.data["path"] = "other/../preview.png"
        self.save_descriptor()
        with self.assertRaisesRegex(ValueError, "bound evidence"):
            self.export()
        self.data.update(checkpoint_path=self.native.name, path=self.native.name, sha256=sha(self.native))
        self.ledger["preview"]["files"][self.native.name] = sha(self.native)
        self.save_descriptor()
        with self.assertRaisesRegex(ValueError, "native file"):
            self.export()

    def test_requires_pinned_descriptor_and_explicit_embedded_model_verification(self):
        self.approval["descriptor_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "not bound"):
            self.export()
        model = self.root / "viewer.glb"
        model.write_bytes(b"model fixture")
        self.ledger["preview"]["files"][model.name] = sha(model)
        self.data.update(checkpoint_path=model.name, path="view/viewer.glb", sha256=sha(model))
        self.save_descriptor()
        with self.assertRaisesRegex(ValueError, "embedded-export"):
            self.export()

    def test_rejects_omitted_qa_and_duplicate_entries(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            export_records(self.root, self.ledger, [self.approval, self.approval])
        self.data["qa"].pop("G2")
        self.save_descriptor()
        with self.assertRaisesRegex(ValueError, "QA and adoption"):
            self.export()
