from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,gzip
p=Path(__file__).parent; s=p.parent/'native';video=s/'pc-four-conditions.webm'
raw=json.load(gzip.open(s/'up-runs.json.gz','rt')); routes=[r for r in raw if r.get('view')=='pc' and r.get('kind')=='field']
plate=Image.new('RGB',(8*160,4*405),'#ddd');d=ImageDraw.Draw(plate);seeks=[]
for mi,mode in enumerate('ABCD'):
 r=next(x for x in routes if x['mode']==mode and x['route']=='straight');start=r['rows'][0]['t']/1000+.08
 for n in range(8):
  t=start+n*.04;f=p/'native-temp.png';subprocess.run(['ffmpeg','-threads','1','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(f)],check=True)
  im=Image.open(f).convert('RGB').crop((335,120,495,500));plate.paste(im,(n*160,mi*405+25));d.text((n*160+2,mi*405+4),f'{mode} {t:.3f}s',fill='black')
  seeks.append({'mode':mode,'seek':t,'crop':[335,120,160,380]})
plate.save(p/'own-native-straight-chronology.png')
# all12 routes, complete image downscaled solely for route overview; no tiny-boot quality claim from this plate.
plate=Image.new('RGB',(1280,12*250),'white');d=ImageDraw.Draw(plate)
for i,r in enumerate(routes):
 for n,dt in enumerate([.15,.5,.85]):
  t=r['rows'][0]['t']/1000+dt;f=p/'native-temp.png';subprocess.run(['ffmpeg','-threads','1','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(f)],check=True)
  plate.paste(Image.open(f).convert('RGB').resize((426,240)),(n*426,i*250+10))
 d.text((1,i*250),f"{r['mode']} {r['route']}",fill='black')
plate.save(p/'own-native-allroutes-overview.png');f.unlink()
(p/'native-seeks.json').write_text(json.dumps({'source':str(video),'record':[1280,720],'temporal_rate':1,'straight_samples':seeks,'note':'Chronological40ms samples; native1:1 pixel crop, no spatial scaling. 25fps capture cannot expose every browser RAF.'},indent=2))
