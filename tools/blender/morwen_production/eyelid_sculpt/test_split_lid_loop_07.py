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



class TestAuditRegressions(TestLoop):
    def test_reverse_anchor_order(self):
        r=split_loop(self.c,[4,0])
        for name in ('chain_A','chain_B'):
            self.assertEqual((r[name][0],r[name][-1]),(4,0))
    def test_duplicate_edge(self):
        self.c['edge_ids'].append([1,0])
        with self.assertRaises(ValueError): split_loop(self.c,[0,4])
    def test_invalid_samples(self):
        for samples in (0,1,2.5,True):
            with self.assertRaises(ValueError): split_loop(self.c,[0,4],samples)
    def test_nonfinite(self):
        self.c['world_xyz_m']['0'][0]=float('nan')
        with self.assertRaises(ValueError): split_loop(self.c,[0,4])
    def test_coincident(self):
        self.c['world_xyz_m']['3']=self.c['world_xyz_m']['0'][:]
        with self.assertRaises(ValueError): split_loop(self.c,[0,4])
    def test_branch(self):
        self.c['edge_ids'].append([0,4])
        with self.assertRaises(ValueError): split_loop(self.c,[0,4])
    def test_missing_edge(self):
        self.c['edge_ids'].pop()
        with self.assertRaises(ValueError): split_loop(self.c,[0,4])
    def test_crossing_proposal(self):
        from correspondence_audit_07 import propose
        self.c['world_xyz_m']={str(i):[math.cos(i*math.pi/4),0,math.sin(i*math.pi/4)] for i in range(8)}
        self.c['world_xyz_m']['1'],self.c['world_xyz_m']['6']=self.c['world_xyz_m']['6'],self.c['world_xyz_m']['1']
        self.assertEqual(propose(self.c)['status'],'BLOCKED_GEOMETRY')

class TestRealModelCapture(unittest.TestCase):
    def test_replay(self):
        import json
        from pathlib import Path
        from correspondence_audit_07 import propose, source_anchor_ids
        root=Path(__file__).parent/'evidence_07'
        topology=json.loads((root/'EYELID_07_TOPOLOGY_MAP.json').read_text())
        baseline=json.loads((root/'EYELID_05_REPORT.json').read_text())
        for side, expected in (('R',[1397,1351]),('L',[1264,1207])):
            c=topology['sides'][side]['components'][0]
            self.assertEqual(len(c['vertex_ids']),28)
            self.assertEqual(len(c['edge_ids']),28)
            self.assertEqual(source_anchor_ids(c,baseline['build']['lid_'+side]['canthus_vertex_world']),expected)
            r=propose(c)
            self.assertEqual(r['anchor_ids'],expected)
            self.assertEqual(r['projected_intersections'],[])
            self.assertEqual(r['anomalous_edges'],[])
            self.assertEqual(len(r['paired_samples']),33)
    def test_source_anchor_missing(self):
        from correspondence_audit_07 import source_anchor_ids
        with self.assertRaises(ValueError):
            source_anchor_ids({'world_xyz_m':{'1':[0,0,0]}},{'inner':[1,0,0],'outer':[2,0,0]})

if __name__=='__main__': unittest.main()
