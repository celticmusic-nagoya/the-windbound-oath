"""Fail-closed reuse decision. Metadata must come from authenticated artifact lookup."""
from datetime import datetime, timezone
import unittest
from two_task_key import task_key
from two_task_artifact import verify

def eligible(root, spec, manifest, metadata, now):
    try:
        key = task_key(spec)
        if metadata.get('expired') is not False or not metadata.get('artifact_id') or not metadata.get('run_id'):
            return False
        expires = datetime.fromisoformat(metadata['expires_at'].replace('Z','+00:00'))
        if now >= expires or metadata.get('task_key') != key:
            return False
        if metadata.get('archive_verified') is not True or metadata.get('provenance_verified') is not True:
            return False
        return verify(root,manifest,key)
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        return False

class Tests(unittest.TestCase):
    def test_legacy_rejected(self):
        self.assertFalse(eligible('.',{}, {},{},datetime.now(timezone.utc)))
    def test_reuse_and_expiry(self):
        import tempfile
        from pathlib import Path
        from two_task_artifact import digest
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            f=root/'output.txt'
            f.write_text('synthetic')
            spec=dict(asset='fixture',stage='preview',method='test',inputs={'in':'a'*64},toolchain={'tool':'b'*64},settings={'qa':'c'*64})
            key=task_key(spec)
            manifest=dict(schema='two.artifact.v1',task_key=key,technical_status='PASS',files={'output.txt':digest(f)})
            meta=dict(expired=False,artifact_id=1,run_id=2,expires_at='2030-01-01T00:00:00Z',task_key=key,archive_verified=True,provenance_verified=True)
            now=datetime(2026,11,21,tzinfo=timezone.utc)
            self.assertTrue(eligible(root,spec,manifest,meta,now))
            for change in ({'expired':True},{'task_key':'d'*64},{'provenance_verified':False},{'expires_at':'2026-01-01T00:00:00Z'}):
                self.assertFalse(eligible(root,spec,manifest,dict(meta,**change),now))
            f.write_text('corrupt')
            self.assertFalse(eligible(root,spec,manifest,meta,now))
if __name__=='__main__':
    unittest.main()
