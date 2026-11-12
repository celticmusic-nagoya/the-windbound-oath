"""Measured vector sources are distinct from derived registration/synthetic gait."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge11_tested', BASE/'bridge11.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
RIG_PATH = BASE.parent/'layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json'


class Bridge11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = bridge.measure(BASE/'measurements/inputs')
        cls.rig = json.loads(RIG_PATH.read_text())
        cls.template = json.loads((BASE/'measurements/inputs/anchor_template.json').read_text())
        cls.mapping = bridge.mappings(cls.m, cls.rig, cls.template, RIG_PATH)

    def test_31_joint_ids_and_parent_tree(self):
        tree = {**self.rig['kinematicTree'], 'pelvis': None}
        self.assertEqual(set(tree), set(bridge.JOINTS))
        self.assertEqual(len(tree),31)
        for jid in tree:
            seen = set()
            node = jid
            while node is not None:
                self.assertNotIn(node,seen)
                seen.add(node)
                self.assertIn(node,tree)
                node = tree[node]

    def test_four_views_classifications(self):
        for rows in self.m['views'].values():
            self.assertEqual(len(rows),31)
            self.assertEqual(sum(p['status']=='MEASURED' for p in rows.values()),16)
            self.assertEqual(sum(p['status']=='DERIVED' for p in rows.values()),2)
            self.assertEqual(sum(p['status']=='UNRESOLVED' for p in rows.values()),13)

    def test_no_fabricated_sole_coordinates(self):
        for rows in self.m['views'].values():
            for jid in ('heelL','heelR','ballL','ballR','toeL','toeR'):
                self.assertEqual(rows[jid]['status'],'UNRESOLVED')
                self.assertIsNone(rows[jid]['xy'])

    def test_anatomical_marker_sides_preserved(self):
        front,back = self.m['views']['front'],self.m['views']['back']
        self.assertGreater(front['shoulderL']['xy'][0],front['shoulderR']['xy'][0])
        self.assertLess(back['shoulderL']['xy'][0],back['shoulderR']['xy'][0])
        self.assertEqual(self.m['views']['left']['shoulderL']['element'].split('=')[-1],'shoulder_L')

    def test_no_shear_reflection_or_nonuniform_scale(self):
        for view,m in self.mapping['views'].items():
            a,b,c,d,tx,ty = m['matrix']
            self.assertGreater(a,0)
            self.assertEqual(a,d)
            self.assertEqual(b,0)
            self.assertEqual(c,0)
            ground = bridge.rig08.affine([192,984],m['matrix'])
            self.assertAlmostEqual(ground[0],600)
            self.assertAlmostEqual(ground[1],1540)
            self.assertEqual(m['classification'],'DERIVED_CANDIDATE')
            self.assertEqual(m['characterFitStatus'],'BLOCKED')

    def test_crop_order_and_full_sheet_mapping(self):
        for i,v in enumerate(bridge.VIEWS):
            m = self.mapping['views'][v]
            self.assertEqual(m['crop'],[i*384,0,384,1024])
            full = [m['crop'][0]+192,984]
            local = [full[0]-m['crop'][0],full[1]]
            self.assertEqual(bridge.rig08.affine(local,m['matrix']),bridge.rig08.affine([192,984],m['matrix']))

    def test_transformed_values_are_never_measured(self):
        for view in self.mapping['views'].values():
            for p in view['joints'].values():
                self.assertNotEqual(p['status'],'MEASURED')

    def test_source_json_disagreement_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            template=copy.deepcopy(self.template)
            template['joints']['front']['crown']=[190,64]
            (root/'anchor_template.json').write_text(json.dumps(template))
            (root/'anchor_template_sheet.svg').write_bytes((BASE/'measurements/inputs/anchor_template_sheet.svg').read_bytes())
            (root/'anchor_template_front.svg').write_bytes((BASE/'measurements/inputs/anchor_template_front.svg').read_bytes())
            with self.assertRaisesRegex(ValueError,'disagree'):
                bridge.measure(root)

    def test_unknown_svg_transform_rejected(self):
        text=(BASE/'measurements/inputs/anchor_template_front.svg').read_text().replace('translate(0,0)','scale(-1,1)')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.svg';path.write_text(text)
            with self.assertRaisesRegex(ValueError,'transform'):
                bridge.markers(path,'front')

    def test_synthetic_hierarchy_movement_and_plant(self):
        data,r = bridge.synthetic(self.rig)
        self.assertTrue(data['synthetic'])
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['hierarchyErrors'],[])
        self.assertTrue(all(all(v.values()) for v in r['armLegMovement'].values()))
        for view,frames in data['tracks'].items():
            self.assertEqual(len(frames),6)
            self.assertEqual([f['timeMs'] for f in frames],[0,100,200,300,400,500])
            self.assertTrue(all(x['maxPairwiseDriftPx']==0 for x in r['results'][view]))

    def test_injected_foot_slide_fails(self):
        data,_=bridge.synthetic(self.rig)
        data['tracks']['left'][1]['actorTransform']['translationPx'][0]+=5
        self.assertEqual(bridge.audit(data,2)['status'],'FAIL')

    def test_invalid_timestamps_fail(self):
        data,_=bridge.synthetic(self.rig)
        data['tracks']['left'][1]['timeMs']=0
        self.assertEqual(bridge.audit(data,2)['status'],'FAIL')

    def test_actual_empty_frames_remain_blocked(self):
        r,_=bridge.audit_real(BASE/'measurements/bridge10_input.json',BASE/'measurements/inputs/REAL_FRAMES_EMPTY_TEMPLATE.json')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertFalse(r['realAssetVerified'])
        self.assertFalse(r['adoptionReady'])


if __name__=='__main__':
    unittest.main()
