"""Summarize measured DEV contour projection; all anatomy/contact labels remain inferred."""
from pathlib import Path
import argparse,json,gzip,statistics,csv
from PIL import Image,ImageDraw
import numpy as np

def summarize(runs):
 summary=[];edges=[]
 for run in runs:
  rows=run['rows'];m={'view':run['view'],'cycle':run['cycle'],'mode':run['mode'],'offset_native':run['foot_offset'],'measured_period':run['measured_period'],'projection_error_world':run['max_projection_error_world'],'wholeframe_origin_range':[min(x['origin_world'] for x in rows),max(x['origin_world'] for x in rows)]}
  m['poses']={str(n):{'gap128_range':[min(x['gap128'] for x in rows if x['frame']==n),max(x['gap128'] for x in rows if x['frame']==n)],'gap200_range':[min(x['gap200'] for x in rows if x['frame']==n),max(x['gap200'] for x in rows if x['frame']==n)]} for n in [1,5,2,6]};summary.append(m)
  for na,nb in [(1,5),(5,2),(2,6),(6,1)]:
   pairs=[(a,b) for a,b in zip(rows,rows[1:]) if a['frame']==na and b['frame']==nb]
   if not pairs:raise AssertionError('missing observed edge')
   edges.append({k:m[k] for k in ['view','cycle','mode','offset_native']}|{'from':na,'to':nb,'samples':len(pairs),'wholeframe_step_after_removing_continuous_bob':statistics.median((b['origin_world']+b['expected_lift'])-(a['origin_world']+a['expected_lift']) for a,b in pairs),'gap128_step_after_removing_continuous_bob':statistics.median((b['gap128']-b['expected_lift'])-(a['gap128']-a['expected_lift']) for a,b in pairs),'raw_wholeframe_step_median':statistics.median(b['origin_world']-a['origin_world'] for a,b in pairs)})
 return {'warning':'Measured DOM projection of annotated alpha-contour probes, not physical contact/naturalness proof. Rendered source pixels are separately captured.','runs':summary,'edges':edges}
def plates(screens,out):
 configurations=[(m,f) for m in ['on','off','quarter'] for f in [0,8]]
 feet=Image.new('RGB',(880,6*160),(26,36,30));wrap=Image.new('RGB',(560,6*270),(26,36,30));df=ImageDraw.Draw(feet);dw=ImageDraw.Draw(wrap)
 for row,(mode,offset) in enumerate(configurations):
  for col,n in enumerate([1,5,2,6]):
   im=Image.open(screens/f'pc-90-{mode}-{offset}-frame{n:02}.png').convert('RGB');a=np.array(im);mask=(a[:,:,0]>220)&(a[:,:,1]>180)&(a[:,:,2]<150);ys=np.where(mask.sum(1)>im.width*.6)[0];ground=int(np.median(ys)) if len(ys) else round(im.height*.8);cx=im.width/2
   q=im.crop((cx-95,ground-100,cx+125,ground+28));feet.paste(q,(col*220,row*160+25));df.text((col*220+5,row*160+5),f'{mode} 06+{offset} / PNG{n:02}',fill='white')
   if n in [6,1]:
    x=0 if n==6 else 280;q=im.crop((cx-120,ground-228,cx+140,ground+14));wrap.paste(q,(x,row*270+25));dw.text((x+4,row*270+4),f'{mode} 06+{offset} / PNG{n:02}',fill='white')
 feet.save(out/'measured-pose-feet.png');wrap.save(out/'measured-wrap06-01.png')
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--screens',type=Path);p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 raw=gzip.decompress(args.raw.read_bytes()) if args.raw.suffix=='.gz' else args.raw.read_bytes();runs=json.loads(raw);result=summarize(runs);(args.out/'measured-summary.json').write_text(json.dumps(result,indent=2))
 with (args.out/'measured-edges.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(result['edges'][0]));w.writeheader();w.writerows(result['edges'])
 if args.screens:plates(args.screens,args.out)
 print('PASS summarized',len(result['runs']),'conditions/views and',len(result['edges']),'observed edges; not physical contact proof')
if __name__=='__main__':main()
