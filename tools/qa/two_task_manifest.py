"""Build a candidate manifest from an explicit output allowlist; no adoption implied."""
import re
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from two_task_key import task_key
from two_task_artifact import digest, verify

def build(root, spec, names, head, run_id, technical_status):
    if not isinstance(head,str) or not re.fullmatch('[0-9a-f]{40}',head) or type(run_id) is not int or run_id <= 0 or technical_status != 'PASS':
        raise ValueError('verified producer and technical result required')
    if not isinstance(names,list) or not names or any(not isinstance(n,str) for n in names) or len(set(names)) != len(names):
        raise ValueError('explicit unique output list required')
    root=Path(root).resolve(strict=True)
    files={}
    for name in names:
        p=PurePosixPath(name)
        if not name or name=='.' or p.is_absolute() or '..' in p.parts or p.as_posix()!=name or chr(92) in name:
            raise ValueError('unsafe output path')
        target=root
        for part in p.parts:
            target=target/part
            if target.is_symlink():
                raise ValueError('symlink')
        if not target.is_file():
            raise ValueError('missing output')
        files[name]=digest(target)
    m=dict(schema='two.artifact.v1',task_key=task_key(spec),technical_status=technical_status,files=files,producer_head=head,run_id=run_id,adoption_status='CANDIDATE_ONLY')
    verify(root,m,m['task_key'])
    return m

class Tests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'preview.txt').write_text('synthetic fixture')
            spec=dict(asset='fixture',stage='preview',method='test',inputs={'source':'a'*64},toolchain={'runtime':'b'*64},settings={'qa':'c'*64})
            m=build(root,spec,['preview.txt'],'d'*40,1,'PASS')
            self.assertTrue(verify(root,m,task_key(spec)))
            self.assertEqual(m['adoption_status'],'CANDIDATE_ONLY')
            for names in ([],['../outside'],['preview.txt','preview.txt'],['missing']):
                with self.assertRaises(ValueError):
                    build(root,spec,names,'d'*40,1,'PASS')
            with self.assertRaises(ValueError):
                build(root,spec,['preview.txt'],'d'*40,1,'FAIL')

if __name__=='__main__':
    unittest.main()
