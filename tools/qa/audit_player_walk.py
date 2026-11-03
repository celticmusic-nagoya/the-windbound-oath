#!/usr/bin/env python3
"""Read-only Phase A metadata/alpha inventory; does not infer anatomical contact or certify gait."""
from pathlib import Path
import argparse,json,hashlib,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def registry(hero):
 s=(ROOT/f'js/field/{hero}-field-assets.js').read_text();marker='const frames = ' if hero=='aidan' else 'frames: Object.freeze('
 return json.JSONDecoder().raw_decode(s.split(marker,1)[1])[0]
def audit():
 rows=[];banks=[]
 for hero in ['aidan','fiona']:
  data=registry(hero)
  for direction in ['up','down','left','right']:
   variants=['walk']+(['side'] if hero=='fiona' and direction in ['left','right'] else [])
   for variant in variants:
    prefix=f'{hero}_{variant}_{direction}_';entries=sorted((k,v) for k,v in data.items() if k.startswith(prefix));n=len(entries)
    assert n==(6 if hero=='aidan' or variant=='side' else 4),(prefix,n)
    banks.append({'hero':hero,'direction':direction,'variant':variant,'frames':n,'cycle_world':180 if hero=='aidan' and direction in ['left','right'] else 90,'phase_annotation':'MISSING: filenames/alpha cannot establish contact foot'})
    for i,(key,m) in enumerate(entries,1):
     assert key==prefix+f'{i:02}'
     p=ROOT/m['path'].split('?')[0];im=Image.open(p);assert im.mode=='RGBA' and im.size==(m['width'],m['height'])
     b=im.getchannel('A').getbbox();assert b and 0<b[0]<b[2]<im.width and 0<b[1]<b[3]<im.height
     assert m['anchor']==([1024,1230] if hero=='aidan' else [640,790])
     rows.append({'hero':hero,'direction':direction,'variant':variant,'key':key,'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'canvas':list(im.size),'bounds_alpha_gt0':list(b),'anchor':m['anchor'],'scale':m['scale'],'alpha_sha256':hashlib.sha256(im.getchannel('A').tobytes()).hexdigest()})
 assert len(rows)==52 and len(banks)==10
 return {'base_main':'e63780543d7ba1719a39a2f68b9924dc6d5b3933','scope':'Phase A only; no revised assets, runtime change or gait-completion PASS','nominal_directions':8,'runtime_walk_banks':10,'walk_pngs':52,'banks':banks,'frames':rows,'limitations':['Contact/left-right anatomical phases require visual/art annotations; no automated alpha-to-contact inference.','Cadence changes cannot create missing opposite-leg poses.','Future candidates require director adoption before production integration.']}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path);args=ap.parse_args();out=audit()
 if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('PASS Phase A metadata/alpha inventory:8 directions /10 banks /52 walk PNGs')
 print('NOT_RUN repaired gait completion; director candidate approval and physical Android pending')
if __name__=='__main__':main()
