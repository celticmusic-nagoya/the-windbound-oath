"""Validate BRIDGE-06 measurement and adapt explicitly supplied real frame tracks to BRIDGE-07."""
import json, math, sys
from pathlib import Path
from contact_audit import audit, VIEWS

REQUIRED = ('heelL','heelR','ballL','ballR','toeL','toeR')
JOINTS = ('ankleL','ankleR','ballL','ballR','chin','elbowL','elbowR','footL','footR','handL','handR','headCenter','headTop','heelL','heelR','hipL','hipR','jawL','jawR','kneeL','kneeR','neckBase','neckTop','shoulderL','shoulderR','toeL','toeR','waist','wristL','wristR','pelvis')

def convert(measurements, real_frames, threshold=2.0):
    issues=[]
    if measurements.get('schema')!='cas/anchor-bridge/measurement-02':issues.append('invalid measurement schema')
    if real_frames.get('schema')!='cas/anchor-real-frames/08':issues.append('invalid real-frame schema')
    if real_frames.get('synthetic') is not False:issues.append('real-frame provenance not confirmed')
    measured=measurements.get('views',{})
    tracks={}
    for direction in VIEWS:
        pts=measured.get(direction,{})
        if not isinstance(pts,dict):pts={}
        for jid in REQUIRED:
            xy=pts.get(jid)
            if not isinstance(xy,list) or len(xy)!=2 or not all(isinstance(z,(int,float)) and math.isfinite(z) and 0<=z<([384,1024][i]) for i,z in enumerate(xy)):
                issues.append(f'{direction}: missing measured {jid}')
        frames=real_frames.get('tracks',{}).get(direction,[])
        if not isinstance(frames,list) or not frames:issues.append(f'{direction}: real frames missing');frames=[]
        out=[]
        for i,frame in enumerate(frames):
            if not isinstance(frame,dict):issues.append(f'{direction}/{i}: invalid frame');continue
            if frame.get('source')!='measured-real-frame':issues.append(f'{direction}/{i}: provenance missing')
            joints=frame.get('joints',{})
            if not isinstance(joints,dict):joints={}
            for jid in JOINTS:
                xy=joints.get(jid)
                if not isinstance(xy,list) or len(xy)!=2 or not all(isinstance(z,(int,float)) and math.isfinite(z) for z in xy):
                    issues.append(f'{direction}/{i}: missing posed joint {jid}')
            out.append({k:frame.get(k) for k in ('timeMs','actorTransform','contacts') } | {'joints':joints})
        tracks[direction]=out
    if issues:return {'status':'BLOCKED','errors':issues,'adoptionReady':False,'realAssetVerified':False},None
    payload={'schema':'cas/anchor-contact-tracks/07','status':'REAL_INPUT_UNVERIFIED','tracks':tracks}
    report=audit(payload,threshold)
    report['source']='bridge08: explicit measured frame inputs; no frame synthesis'
    report['realAssetVerified']=False
    report['adoptionReady']=False
    return report,payload

if __name__=='__main__':
    if len(sys.argv)!=4:sys.exit('usage: python bridge08.py MEASUREMENTS.json REAL_FRAMES.json OUTPUT_PREFIX')
    m=json.loads(Path(sys.argv[1]).read_text());f=json.loads(Path(sys.argv[2]).read_text())
    result,tracks=convert(m,f)
    prefix=Path(sys.argv[3]);prefix.parent.mkdir(parents=True,exist_ok=True)
    prefix.with_suffix('.qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if tracks is not None:prefix.with_suffix('.tracks.json').write_text(json.dumps(tracks,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit({'PASS':0,'FAIL':1,'BLOCKED':2}[result['status']])
