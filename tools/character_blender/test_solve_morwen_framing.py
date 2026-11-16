import unittest
from solve_morwen_framing import solve_framing
class FramingTests(unittest.TestCase):
 def test_observed_case(self):
  x=solve_framing(.8438,.651)
  self.assertEqual(x["status"],"FEASIBLE")
  self.assertGreaterEqual(x["predicted_height"],.72-1e-5)
  self.assertLessEqual(x["predicted_width"],.95)
 def test_impossible_aspect(self):
  self.assertEqual(solve_framing(.95,.3)["status"],"BLOCKED_INFEASIBLE")
 def test_bad_input(self):
  self.assertEqual(solve_framing(0,.8)["status"],"BLOCKED_INVALID_INPUT")
if __name__=="__main__":unittest.main()
