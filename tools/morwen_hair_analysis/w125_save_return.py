"""W125 read-only post-click observer. No GUI clicks, no native save or adoption.
Replaces W124's unqualified Hairstyle Sets marker; existing save/reopen remains required.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, signal, subprocess, time
from pathlib import Path
from PIL import Image

REQUIRED={'Face','Hairstyle','Body','Outfit','Front','Customize','Presets','Custom','Edit Hairstyle','Edit Hair Bounce'}
MODAL={'Close Hairstyle Editor','Save as new item','Items to save','Close without saving','Overwrite','Cancel','Discard','OK','Temporary Items','Save Changes','Save As'}
EDITOR={'Hair Groups','Add Freehand Hair Guides','Add Procedural Hair Guides','Edit Preset','Freehand Guides'}

def classify(text: str, document='Morwen-resume.vroid') -> str:
    tokens={x.strip() for x in re.split(r'[|\r\n]+',text) if x.strip()}
    if tokens & MODAL or any(x.startswith('Do you want to save') for x in tokens): return 'DIALOG_OR_MODAL'
    if tokens & EDITOR: return 'HAIR_EDITOR'
    # Exact dirty model title; a clean model, another document, or main hairstyle tab is not the target.
    title=f'VRoid Studio 2.16.0 - {document}*'
    if title in tokens and REQUIRED <= tokens: return 'FRONT_RETURN_CANDIDATE'
    return 'UNKNOWN'

def verify_png(path: Path):
    with Image.open(path) as image:
        if image.format!='PNG' or image.size!=(1024,768): raise ValueError('unexpected screenshot dimensions/format')
        image.verify()

def run_capture(argv, *, deadline, stdout=None):
    remaining=deadline-time.monotonic()
    if remaining<=0: raise TimeoutError('observer deadline')
    # Start a separate process group so a stuck capture/recognizer cannot outlive the bounded observer.
    proc=subprocess.Popen(argv, stdout=stdout if stdout is not None else subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        rc=proc.wait(timeout=min(12.0,remaining))
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        proc.wait()
        raise TimeoutError('capture timeout')
    if rc: raise RuntimeError(f'capture exited {rc}')

def observe(gui: str, evidence: Path, document='Morwen-resume.vroid', *, max_attempts=30, max_seconds=90., interval=2., capture=run_capture, clock=time.monotonic, sleeper=time.sleep):
    deadline=clock()+max_seconds
    log=evidence/'W125-save-poll.jsonl'
    aliases=[evidence/'W110-save-return.txt',evidence/'W110-save-return.png']
    if log.exists() or any(p.exists() for p in aliases): return 2
    streak=0
    try:
        with log.open('x') as out:
            for i in range(1,max_attempts+1):
                if clock()>=deadline: break
                tag=f'W125-save-poll-{i:02d}'
                png=evidence/(tag+'.png'); txt=evidence/(tag+'.txt')
                if png.exists() or txt.exists(): raise ValueError('stale capture')
                capture([gui,'screenshot',str(png)],deadline=deadline)
                verify_png(png)
                with txt.open('xb') as f: capture([gui,'ocr',str(png)],deadline=deadline,stdout=f)
                if not txt.stat().st_size: raise ValueError('empty OCR')
                state=classify(txt.read_text(encoding='utf-8'),document)
                rec={'index':i,'state':state,'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'text_sha256':hashlib.sha256(txt.read_bytes()).hexdigest()}
                out.write(json.dumps(rec)+'\n');out.flush()
                streak=streak+1 if state=='FRONT_RETURN_CANDIDATE' else 0
                if clock()>=deadline: break
                if streak>=2:
                    # exclusive create, no overwrite; return candidate only, not proof of native persistence.
                    for src,dst in zip((txt,png),aliases):
                        with dst.open('xb') as f:f.write(src.read_bytes())
                    return 0
                if i<max_attempts:sleeper(min(interval,max(0.,deadline-clock())))
    except (OSError,ValueError,RuntimeError,TimeoutError) as exc:
        # Existing caller must fail closed and quarantine evidence; no re-click.
        try:
            with (evidence/'W125-observer-error.json').open('x') as f:json.dump({'status':'CAPTURE_OR_EVIDENCE_FAILURE','error_type':type(exc).__name__},f)
        except OSError:pass
        return 2
    return 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gui',required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--document',default='Morwen-resume.vroid');a=p.parse_args()
    raise SystemExit(observe(a.gui,a.evidence,a.document))
