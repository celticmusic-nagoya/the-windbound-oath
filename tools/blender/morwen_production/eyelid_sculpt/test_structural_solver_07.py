import unittest
import numpy as np
from structural_solver_07 import harmonic_field,compose
from surface_checks_07 import proper_crossing

class HarmonicTests(unittest.TestCase):
    def test_exact_boundary_and_linear_interior(self):
        f=harmonic_field({0,1,2},[(0,1),(1,2)],{0:[0,1],2:[2,0]})
        np.testing.assert_allclose(f[0],[0,1]);np.testing.assert_allclose(f[1],[1,0.5]);np.testing.assert_allclose(f[2],[2,0])
    def test_disconnected_unanchored_rejected(self):
        with self.assertRaises(ValueError):harmonic_field({0,1,2},[(0,1)],{0:[0]})
    def test_independent_controls_and_identity(self):
        base=np.array([[0.,0,0],[1,0,0]]);current=base+2
        upper=(np.array([[0,0,-1],[0,0,0]]),np.array([1.,0]))
        lower=(np.array([[0,0,0],[0,0,1]]),np.array([0.,1]))
        np.testing.assert_array_equal(compose(current,base,[upper,lower],[0,0]),current)
        np.testing.assert_array_equal(compose(current,base,[upper,lower],[1,0]),np.array([[0,0,-1],current[1]]))
        np.testing.assert_array_equal(compose(current,base,[upper,lower],[1,1]),base+upper[0]+lower[0])
    def test_invalid_control(self):
        with self.assertRaises(ValueError):compose(np.zeros((1,3)),np.zeros((1,3)),[(np.zeros((1,3)),np.ones(1))],[2])
    def test_true_crossing(self):
        a=np.array([[0.,0,0],[2,0,0],[0,2,0]])
        b=np.array([[0.5,0.5,-1],[0.5,0.5,1],[1.5,0.5,0]])
        self.assertTrue(proper_crossing(a,b))
    def test_disjoint(self):
        a=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        self.assertFalse(proper_crossing(a,a+[0,0,2]))

if __name__=='__main__':unittest.main()
