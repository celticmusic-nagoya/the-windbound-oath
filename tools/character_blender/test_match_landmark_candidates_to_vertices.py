#!/usr/bin/env python3
import importlib.util,pathlib,unittest
spec=importlib.util.spec_from_file_location("match",pathlib.Path(__file__).with_name("match_landmark_candidates_to_vertices.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def setUp(self):
        self.e={"status":"PASS_GEOMETRY_EVIDENCE_ONLY","source_unchanged":True,"source_sha256":"test",
        "models":{"mesh":{"bounds_world_xyz":{"min":[0,0,0],"max":[1,1,2]},
        "horizontal_sampling_bands_NOT_anatomical_landmarks":{"0.50":{"vertices":[{"index":7,"world_xyz":[0,0,1]}]}}}}}
        self.d={"reviewer_confirmed":False,"marks":[{"model":"mesh","view":"front","landmark":"chin","world_z_candidate":1.01}]}
    def test_sparse_match_is_not_anatomical_approval(self):
        r=m.match(self.d,self.e);self.assertEqual(r["anatomical_qa"],"BLOCKED")
        self.assertEqual(r["matches"][0]["vertex_shortlist_NOT_anatomical_matches"][0]["index"],7)
    def test_confirmed_input_rejected(self):
        self.d["reviewer_confirmed"]=True
        with self.assertRaises(ValueError):m.match(self.d,self.e)
    def test_out_of_bounds_rejected(self):
        self.d["marks"][0]["world_z_candidate"]=5
        with self.assertRaises(ValueError):m.match(self.d,self.e)
    def test_unverified_source_rejected(self):
        self.e["source_unchanged"]=False
        with self.assertRaises(ValueError):m.match(self.d,self.e)
if __name__=="__main__":unittest.main()
