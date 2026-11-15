import unittest
import numpy as np
from contact_geometry_08 import walk_cycle,parameters,shared_columns,shell,triangulate_aperture,inside_polygon
from qa_geometry_08 import edge_audit,proper_triangle_crossing,coplanar_overlap_area

class ContactGeometryTests(unittest.TestCase):
    def test_cycle_rejects_branch(self):
        with self.assertRaises(ValueError):walk_cycle([(0,1),(1,2),(2,0),(0,3)])
    def test_disconnected_cycles(self):
        with self.assertRaises(ValueError):walk_cycle([(0,1),(1,2),(2,0),(3,4),(4,5),(5,3)])
    def test_duplicate_edge(self):
        with self.assertRaises(ValueError):walk_cycle([(0,1),(1,2),(2,0),(1,0)])
    def test_directional_cycle(self):
        self.assertEqual(walk_cycle([(10,20),(20,30),(30,10)]),[10,20,30])
    def test_shared_columns_preserve_all_knots(self):
        a=np.array([[0.,0,0],[.3,0,0],[1,0,0]]);b=np.array([[0.,0,0],[.7,0,0],[1,0,0]])
        u=shared_columns([a,b])
        self.assertTrue(np.any(abs(u-.3)<1e-10));self.assertTrue(np.any(abs(u-.7)<1e-10));self.assertGreaterEqual(len(u),33)
    def test_zero_length_curve_rejected(self):
        with self.assertRaises(ValueError):parameters([[0,0,0],[0,0,0]])
    def test_concave_boundary_and_hole_are_preserved(self):
        outer=np.array([[0.,0],[4,0],[4,4],[2,3],[0,4]])
        inner=np.array([[1.,1],[2,1],[2,2],[1,2]])
        result=triangulate_aperture(outer,inner,spacing=.5)
        vertices=result['vertices'];tris=result['triangles'];points=vertices[tris]
        area=sum(abs(np.linalg.det(np.array([p[1]-p[0],p[2]-p[0]])))/2 for p in points)
        self.assertAlmostEqual(area,13.,places=10) # outer area 14 minus hole area 1
        self.assertTrue(all(not inside_polygon(p.mean(axis=0),inner) for p in points))
        expected=set()
        for offset,n in ((0,5),(5,4)):
            expected.update(tuple(sorted((offset+i,offset+(i+1)%n))) for i in range(n))
        actual={tuple(sorted(map(int,e))) for e in result['segments']}
        self.assertEqual(actual,expected)
    def test_shell_has_opposite_shared_edge_directions(self):
        up=np.array([[0.,0,0],[1,0,1],[2,0,0]]);lo=np.array([[0.,0,0],[1,0,-1],[2,0,0]])
        ou=np.array([[-1.,0,0],[1,0,2],[3,0,0]]);ol=np.array([[-1.,0,0],[1,0,-2],[3,0,0]])
        verts,faces,_,_=shell(up,lo,ou,ol)
        a=edge_audit(faces)
        self.assertEqual(a['boundary_or_nonmanifold_edges'],0);self.assertEqual(a['inconsistent_edge_directions'],0)
        self.assertEqual(len(verts)-a['edge_count']+len(faces),0)
    def test_mismatched_canthus_rejected(self):
        up=np.array([[0.,0,0],[1,0,1],[2,0,0]]);lo=up.copy();lo[0,0]=1
        with self.assertRaises(ValueError):shell(up,lo,up,up)
    def test_noncoplanar_crossing(self):
        a=np.array([[0.,0,0],[2,0,0],[0,2,0]]);b=np.array([[.5,.5,-1],[.5,.5,1],[1.5,.5,0]])
        self.assertTrue(proper_triangle_crossing(a,b))
    def test_coplanar_overlap(self):
        a=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        self.assertAlmostEqual(coplanar_overlap_area(a,a),.5)
    def test_shared_edge_has_no_positive_overlap(self):
        a=np.array([[0.,0,0],[1,0,0],[0,1,0]]);b=np.array([[1.,0,0],[1,1,0],[0,1,0]])
        self.assertAlmostEqual(coplanar_overlap_area(a,b),0)
    def test_separate_planes_do_not_overlap(self):
        a=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        self.assertEqual(coplanar_overlap_area(a,a+[0,0,.001]),0)

class ObstacleConstraintTests(unittest.TestCase):
    def test_eye_clearance_and_fixed_projection(self):
        from obstacle_constraints_08 import clear_eye
        front=np.array([[0.,0,0],[.01,0,0],[0,0,.01]])
        eye=front+[0,.0001,0];tri=np.array([[0,1,2]])
        result,report=clear_eye(front,tri,eye,tri,set())
        np.testing.assert_array_equal(result[:,[0,2]],front[:,[0,2]])
        self.assertTrue(np.all(result[:,1]>=.0009-1e-10))
        self.assertGreater(report['constraint_count'],0)
    def test_infeasible_anchor_is_rejected(self):
        from obstacle_constraints_08 import clear_eye
        front=np.array([[0.,0,0],[.01,0,0],[0,0,.01]])
        with self.assertRaises(ValueError):clear_eye(front,np.array([[0,1,2]]),front+[0,.0001,0],np.array([[0,1,2]]),{0,1,2})

class GateTests(unittest.TestCase):
    def test_card_failure_overrides_skin_only_result(self):
        from combine_qa_08 import combine
        qa={'failures':[],'G3':'PARTIAL'}
        verification={'cage_eye_intersections':{'R':{'proper_crossing_pairs':[],'coplanar_positive_area_pairs':[]}},'opaque_card_samples_inside_cage':{'R':1},'protected_face_data_unchanged':True,'protected_face_key_count':58}
        result=combine(qa,verification)
        self.assertEqual(result['G3'],'FAIL')
        self.assertEqual(result['status'],'DISABLED_FAILED_CANDIDATE')

if __name__=='__main__':unittest.main()
