"""Unit tests for read-only guarded lid-loop splitting."""
import math
import unittest
from split_lid_loop_07 import split_loop

class TestLoop(unittest.TestCase):
    def setUp(self):
        self.c = {"ordered_vertex_ids":list(range(8)),
                  "edge_ids":[[i,(i+1)%8] for i in range(8)],
                  "graph_valid":True,"closed_loop":True,
                  "world_xyz_m":{str(i):[math.cos(i*math.pi/4),math.sin(i*math.pi/4),0] for i in range(8)}}
    def test_split(self):
        r=split_loop(self.c,[0,4])
        self.assertEqual(len(r["paired_samples"]),33)
        self.assertEqual(r["chain_A"][0],r["chain_B"][0])
        self.assertEqual(r["chain_A"][-1],r["chain_B"][-1])
    def test_missing_anchor(self):
        with self.assertRaises(ValueError):split_loop(self.c,[0,99])
    def test_adjacent_anchor(self):
        with self.assertRaises(ValueError):split_loop(self.c,[0,1])
    def test_invalid_edge(self):
        self.c["edge_ids"][0]=[0,3]
        with self.assertRaises(ValueError):split_loop(self.c,[0,4])
    def test_not_loop(self):
        self.c["closed_loop"]=False
        with self.assertRaises(ValueError):split_loop(self.c,[0,4])

if __name__=="__main__":unittest.main()
