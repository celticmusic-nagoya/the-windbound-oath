import copy, hashlib, json, os, sys, tempfile, unittest
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qa_layer_template as q  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TPL = os.path.join(HERE, 'morwen.layer-template.json')


def status(r, name):
    return next(c['status'] for c in r['checks'] if c['name'] == name)


class LayerTemplateTest(unittest.TestCase):
    def setUp(self):
        with open(TPL, encoding='utf-8') as f:
            self.t = json.load(f)
        self.tmp = tempfile.mkdtemp()

    def run_with(self, t):
        p = os.path.join(self.tmp, 't.json')
        with open(p, 'w') as f:
            json.dump(t, f)
        return q.run(p, ROOT)

    def png(self, name, size=(1200, 1600), mode='RGBA', sole=1540):
        a = np.zeros((size[1], size[0], 4), np.uint8)
        a[400:sole + 1, 500:700] = 255
        p = os.path.join(self.tmp, name)
        Image.fromarray(a if mode == 'RGBA' else a[..., :3], mode).save(p)
        return {'path': os.path.relpath(p, ROOT), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}

    def test_repository_template_is_blocked_not_fail(self):
        r = q.run(TPL, ROOT)
        self.assertEqual(r['overall'], 'BLOCKED')
        self.assertEqual(r['counts']['FAIL'], 0)
        for v in q.VIEWS:
            self.assertEqual(status(r, f'{v}:canon_sha'), 'PASS')
            self.assertEqual(status(r, f'{v}:ground_contact'), 'PASS')
            self.assertEqual(status(r, f'L0:{v}:image'), 'BLOCKED')
        self.assertEqual(status(r, 'asym:right_garter:front'), 'NOT_RUN')
        self.assertEqual(status(r, 'asym:right_garter:back'), 'BLOCKED')
        self.assertEqual(status(r, 'asym:right_garter:right'), 'BLOCKED')
        self.assertEqual(status(r, 'asym:bag:left'), 'BLOCKED')
        ids = [a['id'] for a in self.t['asymmetry']]
        self.assertEqual(ids, ['right_garter', 'bag', 'hat_flower', 'hat_ribbon'])
        self.assertFalse(r['adoptionReady'])

    def test_valid_layer_png_passes(self):
        t = copy.deepcopy(self.t)
        t['layers'][0]['views']['front']['image'] = self.png('ok.png')
        r = self.run_with(t)
        self.assertEqual(status(r, 'L0:front:image'), 'PASS')
        self.assertEqual(status(r, 'L0:front:sole_on_ground'), 'PASS')

    def test_bad_pngs_fail(self):
        t = copy.deepcopy(self.t)
        t['layers'][0]['views']['front']['image'] = self.png('small.png', size=(1152, 1536))
        t['layers'][1]['views']['front']['image'] = self.png('rgb.png', mode='RGB')
        bad = self.png('sha.png'); bad['sha256'] = '0' * 64
        t['layers'][2]['views']['front']['image'] = bad
        t['layers'][0]['views']['back']['image'] = self.png('float.png', sole=1500)
        r = self.run_with(t)
        for n in ('L0:front:image', 'L1:front:image', 'L2:front:image', 'L0:back:sole_on_ground'):
            self.assertEqual(status(r, n), 'FAIL', n)
        self.assertEqual(r['overall'], 'FAIL')

    def test_mirroring_shear_and_wrong_side_fail(self):
        t = copy.deepcopy(self.t)
        t['layers'][3]['views']['left']['mirrored'] = True
        t['views']['left']['canonToCanvas']['matrix'][2] = 0.1
        t['asymmetry'][0]['views']['right']['expected'] = 'near (visible)'
        t['asymmetry'][1]['views']['front']['verdict'] = 'ASSUMED_OK'
        r = self.run_with(t)
        self.assertEqual(status(r, 'no_mirroring'), 'FAIL')
        self.assertEqual(status(r, 'left:transform_uniform_no_shear'), 'FAIL')
        self.assertEqual(status(r, 'asym:right_garter:side_rule'), 'FAIL')
        self.assertEqual(status(r, 'asym:bag:front'), 'FAIL')

    def test_canon_sha_tamper_fails(self):
        t = copy.deepcopy(self.t)
        t['views']['front']['canonSource']['sha256'] = 'f' * 64
        self.assertEqual(status(self.run_with(t), 'front:canon_sha'), 'FAIL')


if __name__ == '__main__':
    unittest.main()


import verify_fix_candidate as vf  # noqa: E402


class FixCandidateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        rng = np.random.default_rng(0)
        base = np.zeros((600, 300, 3), np.uint8)
        base[50:580, 80:220] = rng.integers(60, 200, (530, 140, 3))
        self.canon = os.path.join(self.tmp, 'canon.png')
        Image.fromarray(base).save(self.canon)
        self.base = base
        t = {'views': {'back': {'canonSource': {'path': self.canon, 'sha256': hashlib.sha256(open(self.canon, 'rb').read()).hexdigest()}}},
             'correctionTargets': [{'view': 'back', 'zonesCanonPx': [[80, 300, 220, 360]]}]}
        self.tpl = os.path.join(self.tmp, 't.json')
        with open(self.tpl, 'w') as f:
            json.dump(t, f)

    def cand(self, name, edit):
        rgba = np.zeros((600, 300, 4), np.uint8)
        rgba[..., :3] = self.base
        rgba[50:580, 80:220, 3] = 255
        edit(rgba)
        p = os.path.join(self.tmp, name)
        Image.fromarray(rgba, 'RGBA').save(p)
        return p

    def st(self, r, n):
        return next(c['status'] for c in r['checks'] if c['name'] == n)

    def test_target_only_change_passes_technical(self):
        def e(a): a[310:350, 100:200, :3] = 255
        r = vf.run(self.tpl, 'back', self.cand('ok.png', e), 'test fixture', root='/')
        for n in ('size_matches_canon', 'border_alpha_zero', 'opaque_body', 'changes_inside_target', 'no_changes_outside_target'):
            self.assertEqual(self.st(r, n), 'PASS', n)
        self.assertEqual(r['overall'], 'NOT_RUN')
        self.assertFalse(r['adoptionReady'])

    def test_outside_change_and_soft_alpha_fail(self):
        def e(a):
            a[310:350, 100:200, :3] = 255
            a[60:200, 90:210, :3] = 0
            a[50:580, 80:220, 3] = 253
        r = vf.run(self.tpl, 'back', self.cand('bad.png', e), 'test fixture', root='/')
        self.assertEqual(self.st(r, 'no_changes_outside_target'), 'FAIL')
        self.assertEqual(self.st(r, 'opaque_body'), 'FAIL')
        self.assertEqual(r['overall'], 'FAIL')

    def test_missing_candidate_blocked(self):
        r = vf.run(self.tpl, 'back', os.path.join(self.tmp, 'none.png'), root='/')
        self.assertEqual(r['overall'], 'BLOCKED')
