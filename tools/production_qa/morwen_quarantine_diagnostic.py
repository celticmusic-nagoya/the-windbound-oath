"""Read-only exact W118 quarantine diagnostic; no arbitrary output or native mutation."""
import io,json,os,re,sys,zipfile
from pathlib import Path
import morwen_public_recovery as r
ASSET=804538117
SIZE=1393232
DIGEST='369730d0ac791175cc1c964d7c7142bd6a36338e41e91c316f61b3329ec15b11'
RUN='46145481567'
# Only these fixed labels may leave the protected execution environment.
STAGES=[
 ('REOPEN_EVIDENCE','resumed-editor.png'),
 ('FRONT_TAB','W110-before-tab.png'),
 ('FRONT_CATEGORY','W110-before-category.png'),
 ('FRONT_EDITOR','W110-before-editor.png'),
 ('FRAMING','W110-framing.png'),
 ('BRUSH_SCREEN','W110-before-brush.png'),
 ('CAMERA_REGISTRATION','W110-camera-registration.json'),
 ('GUIDE_FIT','W110-fit.json'),
 ('STROKE_PATH','W110-F06-stroke.json'),
 ('STROKE_DISPATCH','W110-F06-dispatch.txt'),
 ('AFTER_STROKE','W110-F06-after.png'),
 ('ALL_VISIBLE','W110-all-visible.png'),
 ('SAVE_DIALOG','W110-save-dialog.png'),
 ('SAVE_CHECKPOINT','W110-checkpoint-receipt.json'),
 ('REOPEN_CHECKPOINT','checkpoint-reopened.png'),
 ('REOPEN_GROUP','W110-reopened-group.png'),
 ('REOPEN_VISIBLE','W110-reopened-visible.png'),
 ('NATIVE_RECEIPT','W110-receipt.json')]
ERRORS=[
 ('F06_SCALE_TOLERANCE','F06 unsupported at scale-adjusted tolerance'),
 ('STALE_FACE_REGISTRATION','stale or invalid face registration'),
 ('REQUIRED_TOOL_INACTIVE','required tool inactive'),
 ('COLLAR_ANCHOR_DETAIL','insufficient collar anchor detail'),
 ('FRONT_GROUP_COUNT','not sole new Front group'),
 ('BLUEPRINT_IDENTITY','blueprint identity'),
 ('W108_FACE_IDENTITY','W108 face registration identity'),
 ('W108_REFERENCE_IDENTITY','W108 reference identity'),
 ('CAMERA_OR_POSE','camera/pose moved'),
 ('FACE_REGISTRATION','face registration residual too high'),
 ('EYE_REGISTRATION','eye registration mismatch'),
 ('GUIDE_SUPPORT','face-registered path outside guide'),
 ('GUIDE_NOT_ESTABLISHED','guide not established'),
 ('GROUP_SELECTION','group selection not verified'),
 ('BRUSH_INACTIVE','brush inactive'),
 ('CHILD_LIST','unexpected visible child list'),
 ('EYE_VISIBILITY','expected visible eye not matched'),
 ('CAMERA_REGISTRATION_OTHER','camera registration'),
 ('JACKET_REGISTRATION','jacket'),
 ('ROW_GUARD','stale row capture'),
 ('DISPLAY','screen resolution'),
 ('SHELL_UNBOUND','unbound variable'),
 ('MISSING_FILE','No such file or directory'),
 ('PERMISSION','Permission denied'),
 ('MISSING_COMMAND','command not found'),
 ('ASSERTION','AssertionError'),
 ('VALUE_ERROR','ValueError'),
 ('FILE_NOT_FOUND','FileNotFoundError'),
 ('PYTHON_IMPORT','ModuleNotFoundError'),
 ('SWIFT_COMPILE','error:'),
]
def inspect(raw):
    r.require(len(raw)==SIZE and r.sha(raw)==DIGEST)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        r.verify_inventory(z)
        names=set(z.namelist())
        r.require({'receipt.json','SHA256SUMS.json'}<=names)
        manifest=json.loads(z.read('SHA256SUMS.json'))
        r.require(isinstance(manifest,dict) and set(manifest)==names-{'SHA256SUMS.json'} and all(r.sha(z.read(n))==v for n,v in manifest.items()))
        rec=json.loads(z.read('receipt.json'))
        r.require(rec.get('status')=='QUARANTINED_FAILED_TRIAL_NOT_ADOPTED' and str(rec.get('public_run_id'))==RUN and rec.get('source_sha256')==r.NATIVE_SHA and rec.get('native_reopen')=='NOT_VERIFIED' and type(rec.get('candidate_present')) is bool and rec['candidate_present']==('quarantined-native.vroid' in names))
        # Never print exception messages, OCR, filenames supplied by the archive, raw logs, model bytes or images.
        log=z.read('gui.log').decode('utf-8','replace') if 'gui.log' in names else ''
        guard=z.read('W110-F06-guard.txt').decode('utf-8','replace') if 'W110-F06-guard.txt' in names else ''
        last=next((label for label,name in reversed(STAGES) if name in names),'PRE_REOPEN')
        # Prefer the terminal Python exception, not arbitrary words in earlier setup output.
        terminal=[line.strip() for line in (log+'\n'+guard).splitlines() if re.match(r'^\s*(ValueError|AssertionError|FileNotFoundError|PermissionError|ModuleNotFoundError)(:|$)',line)]
        message=terminal[-1] if terminal else ''
        code=next((label for label,pattern in ERRORS if pattern in message),'UNCLASSIFIED') if message else next((label for label,pattern in ERRORS if pattern in log or pattern in guard),'UNCLASSIFIED')
        callsite='UNKNOWN'
        if re.search(r'File "[^"\n]*w110_camera_register\.py", line \d+, in support\b',log):callsite='CAMERA_SUPPORT'
        elif re.search(r'File "[^"\n]*w108_guide_fit\.py", line \d+, in context\b',log):callsite='GUIDE_CONTEXT'
        elif re.search(r'File "[^"\n]*w110_camera_register\.py", line \d+, in register\b',log):callsite='CAMERA_REGISTER'
        source_reopen='recovery-result.txt' in names and z.read('recovery-result.txt').strip()==b'REOPENED_READONLY_SOURCE_UNCHANGED'
        return {'stage':last,'error':code,'source_reopen':source_reopen,'candidate_present':rec['candidate_present'],'callsite':callsite}
def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'private-preservation'))
    from release_transport import request
    env=os.environ.copy()
    r.identity(env);token=env['DEST_TOKEN'];r.private(request,token)
    url=r.BASE+'/releases/assets/'+str(ASSET)
    m=request(token,'GET',url)
    r.require(m.get('id')==ASSET and m.get('name')=='Morwen-native-front-quarantine.zip' and m.get('size')==SIZE and m.get('digest')=='sha256:'+DIGEST and m.get('state')=='uploaded')
    result=inspect(request(token,'GET',url,binary=True,limit=SIZE))
    print('QUARANTINE_INTEGRITY_PASS',flush=True)
    print('QUARANTINE_LAST_STAGE_'+result['stage'],flush=True)
    print('QUARANTINE_ERROR_'+result['error'],flush=True)
    print('QUARANTINE_CALLSITE_'+result['callsite'],flush=True)
    print('QUARANTINE_SOURCE_REOPEN_'+('YES' if result['source_reopen'] else 'NO'),flush=True)
    print('QUARANTINE_SAVED_CANDIDATE_'+('YES' if result['candidate_present'] else 'NO'),flush=True)
if __name__=='__main__':
    try:main()
    except Exception:
        print('QUARANTINE_DIAGNOSTIC_BLOCKED',flush=True)
        raise SystemExit(1) from None
