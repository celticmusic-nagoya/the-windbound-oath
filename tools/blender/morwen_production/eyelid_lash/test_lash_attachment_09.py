"""Unit tests for EYELID-09 attachment math; no Blender dependency."""
import unittest
from lash_attachment_09 import evaluated_root,offset_root,dot

class AttachmentTests(unittest.TestCase):
    def setUp(self): self.v=[(0,0,0),(1,0,0),(0,0,1)]
    def test_position(self):
        self.assertEqual(evaluated_root(self.v,(0,1,2),(.25,.25,.5))["position"],(.25,0,.5))
    def test_deformed(self):
        moved=[(x,y+.1,z) for x,y,z in self.v]
        self.assertAlmostEqual(evaluated_root(moved,(0,1,2),(.25,.25,.5))["position"][1],.1)
    def test_reversed_winding(self):
        a=evaluated_root(self.v,(0,1,2),(.25,.25,.5))
        b=evaluated_root(self.v,(0,2,1),(.25,.5,.25))
        self.assertEqual(a["normal"],b["normal"])
    def test_offset(self):
        self.assertAlmostEqual(offset_root(self.v,(0,1,2),(.25,.25,.5),.0001)["root_position"][1],.0001)
    def test_bad_weights(self):
        with self.assertRaises(ValueError): evaluated_root(self.v,(0,1,2),(.4,.4,.4))
    def test_duplicate_index(self):
        with self.assertRaises(ValueError): evaluated_root(self.v,(0,0,2),(.2,.3,.5))
    def test_orthogonal(self):
        f=evaluated_root(self.v,(0,1,2),(.2,.3,.5))
        self.assertAlmostEqual(dot(f["normal"],f["tangent"]),0)
        self.assertAlmostEqual(dot(f["binormal"],f["tangent"]),0)

if __name__=="__main__": unittest.main()
