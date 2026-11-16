"""Non-Blender smoke tests for the EYELID-09 candidate strip scaffold."""
import unittest
from lash_attachment_09 import evaluated_root
from lash_strip_geometry_09 import build_lash_strip

class LashStripTests(unittest.TestCase):
    def setUp(self):
        self.frame=evaluated_root([(0,0,0),(1,0,0),(0,0,1)],(0,1,2),(.2,.3,.5))
    def test_topology(self):
        m=build_lash_strip(self.frame,.01,.002,samples=5)
        self.assertEqual(len(m["vertices"]),10)
        self.assertEqual(len(m["faces"]),4)
        self.assertEqual(len(m["uv"]),10)
    def test_tip_tapers(self):
        m=build_lash_strip(self.frame,.01,.002)
        self.assertGreater(sum((a-b)**2 for a,b in zip(m["vertices"][-1],m["vertices"][-2])),0)
    def test_all_quads_non_degenerate(self):
        from lash_attachment_09 import cross, sub, dot
        m=build_lash_strip(self.frame,.01,.002,samples=9)
        for a,b,c,d in m["faces"]:
            area=cross(sub(m["vertices"][b],m["vertices"][a]),sub(m["vertices"][d],m["vertices"][a]))
            self.assertGreater(dot(area,area),1e-24)
    def test_root_offset(self):
        m=build_lash_strip(self.frame,.01,.002,root_offset_m=.0002)
        self.assertAlmostEqual(m["vertices"][0][1],self.frame["position"][1]+.0002)
    def test_bad_length(self):
        with self.assertRaises(ValueError):build_lash_strip(self.frame,0,.002)
    def test_bad_samples(self):
        with self.assertRaises(ValueError):build_lash_strip(self.frame,.01,.002,samples=2)
    def test_no_collision_claim(self):
        m=build_lash_strip(self.frame,.01,.002)
        self.assertEqual(m["metadata"]["collision_qa"],"NOT_RUN")
if __name__=="__main__":unittest.main()
