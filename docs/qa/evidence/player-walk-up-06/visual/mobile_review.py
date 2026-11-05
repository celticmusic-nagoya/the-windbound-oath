from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,subprocess,gzip
p=argparse.ArgumentParser();p.add_argument('--screens',required=True);p.add_argument('--view',required=True);p.add_argument('--out',required=True);q=p.parse_args();s=Path(q.screens);o=Path(q.out);raw=json.load(gzip.open(s/'up-runs.json.gz','rt'));video=s/f'{q.view}-four-conditions.webm';rows=[];seeks=[]
for mode in 'AB':
 r=next(r for r in raw if r.get('view')==q.view and r.get('mode')==mode and r.get('kind')=='field' and r.get('route')=='straight');start=r['rows'][0]['t']/1000+.12
 ims=[]
 for n in range(8):
  t=start+n*.04;f=o/'mobile-temp.png';subprocess.run(['ffmpeg','-threads','1','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(f)],check=True);im=Image.open(f).convert('RGB');box=(130,330,290,590) if q.view=='portrait' else (120,60,280,320);ims.append(im.crop(box));seeks.append({'mode':mode,'t':t,'crop':list(box)})
 rows.append(ims)
plate=Image.new('RGB',(160*8,285*2),'#ccc');d=ImageDraw.Draw(plate)
for j,ims in enumerate(rows):
 for n,im in enumerate(ims):plate.paste(im,(160*n,285*j+25));d.text((160*n+2,285*j+4),'AB'[j]+f' +{n*.04:.2f}s',fill='black')
plate.save(o/f'own-final-{q.view}-AB-chronology.png');(o/'mobile-temp.png').unlink();(o/f'{q.view}-seeks.json').write_text(json.dumps({'source':str(video),'samples':seeks,'spatial_scale':1,'sample_step_seconds':.04},indent=2))
