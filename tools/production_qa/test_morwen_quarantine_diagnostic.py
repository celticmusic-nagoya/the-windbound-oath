"""No credentials; synthetic archive and failure controls."""
import json,unittest
from unittest.mock import patch
import morwen_quarantine_diagnostic as d
import morwen_public_recovery as r
from test_morwen_public_recovery import archive
def fixture(log,extra=None):
    members={'gui.log':log.encode(),'receipt.json':json.dumps(dict(status='QUARANTINED_FAILED_TRIAL_NOT_ADOPTED',public_run_id=d.RUN,source_sha256=r.NATIVE_SHA,native_reopen='NOT_VERIFIED',candidate_present=False)).encode()}
    members.update(extra or {})
    members['SHA256SUMS.json']=json.dumps({k:r.sha(v) for k,v in members.items()}).encode()
    return archive(members)
class Test(unittest.TestCase):
    def test_fixed_classification(self):
        raw=fixture('untrusted private text; ValueError: face-registered path outside guide',{'W110-before-brush.png':b'synthetic','recovery-result.txt':b'REOPENED_READONLY_SOURCE_UNCHANGED'})
        with patch.multiple(d,SIZE=len(raw),DIGEST=r.sha(raw)):
            self.assertEqual(d.inspect(raw),dict(stage='BRUSH_SCREEN',error='GUIDE_SUPPORT',source_reopen=True,candidate_present=False,callsite='UNKNOWN'))
            with self.assertRaises(ValueError):d.inspect(raw[:-1]+b'x')
    def test_scale_tolerance_and_terminal_precedence(self):
        raw=fixture('jacket setup\n  File "/private/tools/w110_camera_register.py", line 20, in support\nValueError: F06 unsupported at scale-adjusted tolerance',{'W110-camera-registration.json':b'synthetic'})
        with patch.multiple(d,SIZE=len(raw),DIGEST=r.sha(raw)):
            result=d.inspect(raw)
            self.assertEqual(result['error'],'F06_SCALE_TOLERANCE')
            self.assertEqual(result['callsite'],'CAMERA_SUPPORT')
    def test_no_raw_text(self):
        raw=fixture('PRIVATE_RAW_VALUE')
        with patch.multiple(d,SIZE=len(raw),DIGEST=r.sha(raw)):
            self.assertEqual(d.inspect(raw)['error'],'UNCLASSIFIED')
    def test_receipt_cannot_promote(self):
        raw=fixture('x',{'quarantined-native.vroid':b'x'})
        with patch.multiple(d,SIZE=len(raw),DIGEST=r.sha(raw)):
            with self.assertRaises(ValueError):d.inspect(raw)
if __name__=='__main__':unittest.main()
