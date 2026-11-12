"""Read-only real input preflight and drift audit. Never synthesizes frames."""
import argparse, json, hashlib, math
from pathlib import Path
from bridge08 import convert, VIEWS, JOINTS, REQUIRED

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(measurement_path, frame_path, threshold=2.0):
    m=json.loads(Path(measurement_path).read_text(encoding='utf-8'))
    f=json.loads(Path(frame_path).read_text(encoding='utf-8'))
    issues=[]
    if not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or threshold<0:
        raise ValueError('threshold must be finite and nonnegative')
    # Explicit input provenance is required; a user-supplied flag alone is not independent proof.
    for view in VIEWS:
        frames=f.get('tracks',{}).get(view,[])
        if isinstance(frames,list):
            for i,frame in enumerate(frames):
                if not isinstance(frame,dict): continue
                if frame.get('source')=='measured-real-frame' and not frame.get('imageSha256'):
                    issues.append(f'{view}/{i}: frame image SHA-256 missing (not verified by adapter)')
    result,tracks=convert(m,f,threshold)
    if issues:
        result['status']='BLOCKED'
        result.setdefault('errors',[]).extend(issues)
        tracks=None
    result.update({'task':'ANCHOR-RIG-BRIDGE-10','inputSha256':{'measurements':sha(measurement_path),'frames':sha(frame_path)},'realAssetVerified':False,'adoptionReady':False,'productionReady':False,'frameImageShaVerified':False})
    return result,tracks

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('measurements');p.add_argument('frames');p.add_argument('--out',default='bridge10.qa.json');p.add_argument('--threshold',type=float,default=2.0)
    a=p.parse_args();r,tracks=run(a.measurements,a.frames,a.threshold)
    Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    if tracks is not None:
        Path(a.out).with_suffix('.tracks.json').write_text(json.dumps(tracks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':r['status'],'errors':len(r.get('errors',[])),'report':a.out},ensure_ascii=False))
    raise SystemExit({'PASS':0,'FAIL':1,'BLOCKED':2}[r['status']])
