"""Landmark-based screen QA; no automatic segmentation or physical inference."""
import argparse, hashlib, io, itertools, json, math
from pathlib import Path
from PIL import Image
import numpy as np

def sha(b): return hashlib.sha256(b).hexdigest()
def interval(fn, vals, u):
    a=[fn(*v) for v in itertools.product(*[(x-u,x+u) for x in vals])]
    return [min(a),max(a)]
def verdict(a,low,high):
    return 'PASS' if low<=a[0] and a[1]<=high else 'OUTSIDE' if a[1]<low or a[0]>high else 'HOLD'
def measure(raw,spec):
    if sha(raw)!=spec['png_sha256']: raise ValueError('image digest mismatch')
    im=Image.open(io.BytesIO(raw)); im.load(); a=np.asarray(im.convert('RGB'))
    h,w=a.shape[:2]; u=spec['edge_uncertainty_px']
    if not isinstance(u,(int,float)) or not 0<=u<=8: raise ValueError('uncertainty')
    x0,x1=spec['skirt_x']; p0,p1=spec['plaid_x']; y0,y1=spec['skirt_y']; y=spec['sample_y']
    if not (0<=x0<p0<p1<x1<w and 0<=y0<=y<=y1<h and x1-x0>2*u and y1-y0>2*u and p1-p0>2*u): raise ValueError('landmark order')
    width=interval(lambda l,r,p,q:(q-p)/(r-l),[x0,x1,p0,p1],u)
    center=interval(lambda l,r,p,q:((p+q)/2-l)/(r-l),[x0,x1,p0,p1],u)
    height=[y1-y0-2*u,y1-y0+2*u]
    metrics={'visible_height_px':{'value':y1-y0,'interval':height,'status':verdict(height,292,math.inf)},'plaid_width_fraction':{'value':(p1-p0)/(x1-x0),'interval':width,'status':verdict(width,.14,.26)},'plaid_centroid':{'value':((p0+p1)/2-x0)/(x1-x0),'interval':center,'status':verdict(center,.32,.42)}}
    if 'dark_roi' in spec:
        l,t,r,b=spec['dark_roi'];
        if not(0<=l<r<=w and 0<=t<b<=h): raise ValueError('dark roi')
        if not ((x0<=l<r<=p0 or p1<=l<r<=x1) and y0<=t<b<=y1): raise ValueError('dark roi outside unpatterned skirt')
        rgb=a[t:b,l:r]; v=rgb.max(axis=-1)/255
        metrics['dark_roi']={'median_rgb':np.median(rgb,axis=(0,1)).tolist(),'median_v':float(np.median(v)),'status':'DIAGNOSTIC_ONLY','note':'screen sRGB; ROI annotation and lighting require review'}
    if 'lower_gold_bottom_y' in spec:
        g=spec['lower_gold_bottom_y']
        if not y0<g<y1: raise ValueError('gold position')
        f=interval(lambda top,hem,rule:(hem-rule)/(hem-top),[y0,y1,g],u)
        metrics['lower_gold_hem_fraction']={'value':(y1-g)/(y1-y0),'interval':f,'status':verdict(f,.04,.08)}
    eligible=(spec['candidate']=='C1' and spec['view']=='front' and spec['capture_mode']=='normal_preview' and metrics['visible_height_px']['status']=='PASS')
    return {'image_sha256':sha(raw),'candidate':spec['candidate'],'view':spec['view'],'capture_mode':spec['capture_mode'],'manual_landmarks':spec,'metrics':metrics,'eligible_for_C1_front_measurement':eligible,'G2':'NOT_RUN','note':'Human annotation required; eligibility is not verification of identity, camera, four views, geometry, or independent G2.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('png');p.add_argument('landmarks');p.add_argument('output');a=p.parse_args();result=measure(Path(a.png).read_bytes(),json.loads(Path(a.landmarks).read_text()));Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
