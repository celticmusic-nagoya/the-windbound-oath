#!/usr/bin/env python3
"""Offline contract tests for resumable TWO checkpoints; no render or API usage."""
import json
import tempfile
import unittest
from pathlib import Path
from two_checkpoint import build, validate

class Args:
    asset="morwen"
    stage="visual_qa_handoff"
    owner="unassigned"
    pr=427
    branch="feature/morwen-artdirected-sculpt-20261119"
    head_sha="a"*40
    blueprint_sha=""
    method_family="evidence_handoff"
    next_action="independent_art_review"

class CheckpointTests(unittest.TestCase):
    def test_deterministic_evidence_and_change_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"render.png").write_bytes(b"test render A")
            args=Args()
            args.evidence=str(root)
            first=build(args)
            second=build(args)
            self.assertEqual(first,second)
            self.assertEqual(first["gates"]["G2"],"NOT_RUN")
            self.assertEqual(first["status"],"WAITING_FOR_ART_QA")
            (root/"render.png").write_bytes(b"test render B")
            third=build(args)
            self.assertNotEqual(first["input_fingerprint_sha256"],third["input_fingerprint_sha256"])
    def test_reject_invalid_status_and_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"evidence.png").write_bytes(b"evidence")
            args=Args()
            args.evidence=str(root)
            data=build(args)
            data["gates"]["G2"]="APPROVED"
            with self.assertRaises(ValueError): validate(data)
            data["gates"]["G2"]="NOT_RUN"
            data["status"]="UNKNOWN"
            with self.assertRaises(ValueError): validate(data)
    def test_reject_unreviewed_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"evidence.png").write_bytes(b"evidence")
            args=Args()
            args.evidence=str(root)
            data=build(args)
            data["status"]="NEXT_STAGE_READY"
            data["next_action"]="adopt"
            with self.assertRaises(ValueError): validate(data)

if __name__=="__main__":
    unittest.main()
