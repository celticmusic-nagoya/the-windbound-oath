import json, math, sys
from pathlib import Path
VIEWS=('front','right','left','back')
FEET=('L','R')
CONTACTS=('heel','ball','toe')

def audit(data, max_drift_px=2.0):
    errors=[]; warnings=[]; results={}
    if data.get('schema')!='cas/anchor-contact-tracks/07':errors.append('schema mismatch')
    for direction in VIEWS:
        frames=data.get('tracks',{}).get(direction)
        if not isinstance(frames,list) or not frames:
            errors.append(f'{direction}: missing frames');continue
        previous=-float('inf'); stance={}; tracks=[]
        for i,f in enumerate(frames):
            tag=f'{direction}/{i}'
            t=f.get('timeMs')
            if not isinstance(t,(int,float)) or not math.isfinite(t) or t<=previous:
                errors.append(tag+': timeMs not increasing');continue
            previous=t
            tr=f.get('actorTransform',{})
            try:
                x,y=tr['translationPx']; scale=tr['scale']; angle=tr['rotationDeg']
                if not all(math.isfinite(z) for z in (x,y,scale,angle)) or scale<=0:raise ValueError()
            except (KeyError,ValueError,TypeError):errors.append(tag+': invalid transform');continue
            joints=f.get('joints',{})
            for foot in FEET:
                sample=f.get('contacts',{}).get(foot)
                if sample is None:continue
                sid=sample.get('stanceId');part=sample.get('part')
                if not isinstance(sid,str) or not sid or part not in CONTACTS:
                    errors.append(tag+f': {foot} invalid contact');continue
                key=part+foot
                xy=joints.get(key)
                if not isinstance(xy,list) or len(xy)!=2 or not all(isinstance(z,(int,float)) and math.isfinite(z) for z in xy):
                    errors.append(tag+f': {key} missing posed joint');continue
                theta=math.radians(angle);a,b=xy
                world=(x+scale*(math.cos(theta)*a-math.sin(theta)*b),y+scale*(math.sin(theta)*a+math.cos(theta)*b))
                k=(foot,sid)
                if k not in stance:stance[k]=[]
                stance[k].append((i,world))
        for (foot,sid),samples in stance.items():
            if len(samples)<2:
                warnings.append(f'{direction}/{foot}/{sid}: fewer than two contact samples');continue
            indices=[i for i,_ in samples]
            if any(b!=a+1 for a,b in zip(indices,indices[1:])):errors.append(f'{direction}/{foot}/{sid}: non-contiguous stance')
            positions=[p for _,p in samples]
            drift=max(math.dist(a,b) for a in positions for b in positions)
            tracks.append({'foot':foot,'stanceId':sid,'samples':len(samples),'maxPairwiseDriftPx':round(drift,6),'pass':drift<=max_drift_px})
            if drift>max_drift_px:errors.append(f'{direction}/{foot}/{sid}: drift {drift:.3f}px > {max_drift_px}px')
        results[direction]=tracks
    status='FAIL' if errors else 'BLOCKED' if warnings or not any(results.values()) else 'PASS'
    return {'status':status,'thresholdPx':max_drift_px,'errors':errors,'warnings':warnings,'results':results,'realAssetVerified':False,'adoptionReady':False}

if __name__=='__main__':
    if len(sys.argv)!=2:sys.exit('usage: python contact_audit.py TRACKS.json')
    report=audit(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    sys.exit({'PASS':0,'FAIL':1,'BLOCKED':2}[report['status']])
