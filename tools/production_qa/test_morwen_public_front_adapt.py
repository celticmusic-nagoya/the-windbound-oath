"""Synthetic source controls and bounded visibility adapter contract."""
import unittest
from pathlib import Path
import morwen_public_front_adapt as a
class Test(unittest.TestCase):
    def fixture(self):
        return ('# fixture\n'+a.BEGIN+'eyes W110-before-brush 5 0\nready=W110-before-brush\nhidden=0\n'+a.END+'"\u0024anchor" evidence/W110-before-brush-rows.json "$registration")\n# save and reopen untouched\n').encode()
    def test_exact_change(self):
        raw=self.fixture();out=a.adapt(raw,a.git_sha(raw)).decode()
        self.assertIn(a.REPLACEMENT,out)
        self.assertIn('"evidence/$ready-rows.json"',out)
        self.assertTrue(out.endswith('# save and reopen untouched\n'))
        self.assertNotIn(a.BEGIN,out)
    def test_wrong_pin(self):
        with self.assertRaises(ValueError):a.adapt(self.fixture())
    def test_changed_block(self):
        raw=self.fixture().replace(b'hidden=0',b'hidden=1')
        with self.assertRaises(ValueError):a.adapt(raw,a.git_sha(raw))
    def test_duplicate_anchor(self):
        raw=self.fixture()*2
        with self.assertRaises(ValueError):a.adapt(raw,a.git_sha(raw))
    def test_visibility_contract(self):
        s=Path(__file__).with_name('morwen_public_front_visibility.sh').read_text()
        self.assertEqual(s.count('"$gui" click'),1)
        self.assertIn('F06 unsupported at scale-adjusted tolerance',s)
        self.assertIn('eyes W110-isolated 5 4',s)
        self.assertIn('tools/w109_visibility.py change',s)
        self.assertIn('tools/w110_camera_register.py support evidence/W110-isolated.png',s)
        self.assertNotIn('hair-stroke-qualification',s)
if __name__=='__main__':unittest.main()
