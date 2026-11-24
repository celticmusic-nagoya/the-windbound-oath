"""Offline regression tests for the metadata-only Studio discovery audit."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).with_name("audit-discovery.py")
spec = importlib.util.spec_from_file_location("studio_discovery_audit", SCRIPT)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class AuditDiscoveryTests(unittest.TestCase):
    def test_counts_only_unexpired_unpinned_artifacts(self):
        branch = "feature/lind-home-01"
        run = {"id": 11, "head_branch": branch, "head_repository": {"full_name": "owner/repo"}, "head_sha": "a" * 40}
        artifacts = [
            {"id": 101, "name": "new", "expired": False, "size_in_bytes": 42},
            {"id": 102, "name": "expired", "expired": True, "size_in_bytes": 42},
            {"id": 103, "name": "pinned", "expired": False, "size_in_bytes": 42},
            {"id": 104, "name": "empty", "expired": False, "size_in_bytes": 0},
        ]
        def fake_api(repo, path):
            if path.startswith("actions/runs?"):
                return {"workflow_runs": [run] if f"branch={branch}&" in path else []}
            if path == "actions/runs/11/artifacts?per_page=100":
                return {"artifacts": artifacts}
            raise AssertionError(path)
        with patch.object(audit_module, "api", fake_api):
            result = audit_module.audit("owner/repo", 10, {"entries": [{"path": "x"}]}, [{"artifact_id": 103}], {"entries": [{"artifact_id": 104}, {"artifact_id": 105}]})
        self.assertEqual(result["main_seed_manifest_entries"], 1)
        self.assertEqual(result["published_branch_entries"], 2)
        self.assertTrue(next(x for x in result["candidates"] if x["artifact_id"] == 101)["already_published_artifact"] is False)
        self.assertEqual(result["artifacts_seen"], 4)
        self.assertEqual(result["unexpired_unpinned_artifacts"], 1)
        self.assertEqual(result["unexpired_unpinned_by_category"], {"village": 1})
        self.assertEqual(result["candidates"][0]["artifact_id"], 101)
        self.assertEqual(result["status"], "METADATA_ONLY_NOT_APPROVED_FOR_PUBLICATION")

    def test_rejects_foreign_repository_runs(self):
        branch = next(iter(audit_module.BRANCHES))
        def fake_api(repo, path):
            if path.startswith("actions/runs?") and f"branch={branch}&" in path:
                return {"workflow_runs": [{"id": 12, "head_branch": branch, "head_repository": {"full_name": "other/repo"}, "head_sha": "b" * 40}]}
            return {"workflow_runs": []}
        with patch.object(audit_module, "api", fake_api):
            result = audit_module.audit("owner/repo", 1, {"entries": []}, [])
        self.assertEqual(result["artifacts_seen"], 0)


class ZipInspectionTests(unittest.TestCase):
    def test_signatures_duplicates_and_budget(self):
        import tempfile
        import zipfile
        script = pathlib.Path(__file__).with_name("inspect-candidate-zips.py")
        spec = importlib.util.spec_from_file_location("zip_inspector", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "candidate.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("valid.png", b"\x89PNG\r\n\x1a\n")
                archive.writestr("VALID.PNG", b"\x89PNG\r\n\x1a\n")
                archive.writestr("fake.jpg", b"not an image")
                archive.writestr("../unsafe.png", b"\x89PNG\r\n\x1a\n")
            result = module.inspect_zip(path)
            self.assertEqual(result["safe_images"], 1)
            self.assertEqual(result["rejected_members"], 3)
            with patch.object(module, "MAX_TOTAL", 1):
                with self.assertRaisesRegex(ValueError, "aggregate"):
                    module.inspect_zip(path)


if __name__ == "__main__":
    unittest.main()
