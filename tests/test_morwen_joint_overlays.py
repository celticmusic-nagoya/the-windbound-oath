"""Tests for MORWEN-RIG-07; does not require reference images."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/blender"))
from render_morwen_joint_overlays import svg_for
from qa_morwen_anchors import validate

class OverlayTest(unittest.TestCase):
    def test_incomplete_measurements_blocked(self):
        p=json.loads((ROOT/"tools/blender/profiles/morwen_anchors_v1.json").read_text())
        self.assertTrue(validate(p,require_measured=True))
    def test_svg_has_edges_and_points(self):
        names=["head","shoulder.L","shoulder.R","elbow.L","elbow.R","wrist.L","wrist.R","pelvis","knee.L","knee.R","ankle.L","ankle.R"]
        anchors={n:{"x":0.5,"y":0.5} for n in names}
        s=svg_for("front",anchors)
        self.assertEqual(s.count("<circle"),12)
        self.assertEqual(s.count("<line"),14)
    def test_cli_refuses_unmeasured_input(self):
        with tempfile.TemporaryDirectory() as td:
            r=subprocess.run([sys.executable,str(ROOT/"tools/blender/render_morwen_joint_overlays.py"),"--anchors",str(ROOT/"tools/blender/profiles/morwen_anchors_v1.json"),"--output-dir",td],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(list(Path(td).iterdir()),[])

if __name__=="__main__":
    unittest.main()
