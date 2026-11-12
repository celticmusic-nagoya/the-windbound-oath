"""Pure Python contract checks; no Blender installation required."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("shared_rig_adapter",HERE/"shared_rig_adapter.py")
adapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
TOPO=json.loads((HERE/"shared_rig_topology.json").read_text(encoding="utf-8"))

def sample():
    joints=TOPO["joints"]
    # Synthetic fixture ONLY, never use as a real character measurement.
    return {"schema":"cas/blender-measured/01","characterId":"synthetic",
            "sourceSha256":"a"*64,"rigSize":[1200,1600],
            "joints":{name:[600,800] for name in joints}}

class RigContractTests(unittest.TestCase):
    def test_source_topology(self):
        self.assertEqual(len(TOPO["joints"]),31)
        self.assertEqual(sum(v["parent"] is None for v in TOPO["joints"].values()),1)
        for name,entry in TOPO["joints"].items():
            if entry["parent"] is not None:
                self.assertIn(entry["parent"],TOPO["joints"])
    def test_valid_synthetic(self):
        self.assertEqual(len(adapter.validate(TOPO,sample())[0]),31)
    def test_missing_joint_blocks(self):
        data=sample();data["joints"].pop("pelvis")
        with self.assertRaises(ValueError):adapter.validate(TOPO,data)
    def test_unverified_sha_blocks(self):
        data=sample();data["sourceSha256"]="UNVERIFIED"
        with self.assertRaises(ValueError):adapter.validate(TOPO,data)
    def test_out_of_bounds_blocks(self):
        data=sample();data["joints"]["headTop"]=[-1,0]
        with self.assertRaises(ValueError):adapter.validate(TOPO,data)
    def test_nan_blocks(self):
        data=sample();data["joints"]["headTop"]=[float("nan"),0]
        with self.assertRaises(ValueError):adapter.validate(TOPO,data)

if __name__=="__main__":unittest.main()
