from pathlib import Path
import argparse,subprocess,json,gzip
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--video',required=True);p.add_argument('--telemetry',required=True);p.add_argument('--out',required=True);q=p.parse_args();out=Path(q.out);out.mkdir(parents=True,exist_ok=True);r=Path(q.repo);raw=json.load(gzip.open(q.telemetry,'rt') if str(q.telemetry).endswith('.gz') else open(q.telemetry));seeks=[]
plate=Image.new('RGB',(160*10,525*2),'#bbb');d=ImageDraw.Draw(plate)
for mi,mode in enumerate('AB'):
 row=next(x for x in raw if x.get('mode')==mode and x.get('kind')=='field' and x.get('route')=='straight');start=row['rows'][0]['t']/1000+.1
 for n in range(10):
  t=start+n*.04;f=out/'temp.png';subprocess.run(['ffmpeg','-threads','1','-v','error','-ss',str(t),'-i',q.video,'-frames:v','1','-y',str(f)],check=True);im=Image.open(f).convert('RGB').crop((335,100,495,600));plate.paste(im,(n*160,mi*525+25));d.text((n*160+3,mi*525+4),f'{mode} {t:.3f}',fill='black')
 seeks.append({'mode':mode,'start':start,'duration':.9,'crop':[335,100,160,500]})
 subprocess.run(['ffmpeg','-threads','1','-v','error','-ss',str(start),'-i',q.video,'-t','0.9','-vf',f'crop=160:500:335:100,drawtext=text={mode}:fontcolor=white:fontsize=16:x=4:y=4','-an','-threads','1','-y',str(out/f'actual-{mode}.mp4')],check=True)
plate.save(out/'own-actual-4vs5-chronology.png')
subprocess.run(['ffmpeg','-v','error','-i',str(out/'actual-A.mp4'),'-i',str(out/'actual-B.mp4'),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-threads','1','-y',str(out/'own-actual-4vs5-temporal1x.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-i',str(out/'own-actual-4vs5-temporal1x.mp4'),'-vf','scale=960:1500:flags=neighbor','-threads','1','-y',str(out/'own-actual-4vs5-temporal1x-spatial3x.mp4')],check=True)
(out/'motion-seeks.json').write_text(json.dumps({'source':q.video,'telemetry':q.telemetry,'resolution':[1280,720],'rate':1,'seeks':seeks},indent=2))
# Native new boundaries; no alignment or pose warping.
b=r/'assets/candidates/player-walk-polish01/up-06-left-boot-outline/aidan_walk_up_pushoff_candidate_v2.png';imgs={'06':r/'img/field/characters/aidan/aidan_walk_up_06.png','NEW':b,'03':r/'img/field/characters/aidan/aidan_walk_up_03.png'}
for pair in [('06','NEW'),('NEW','03')]:
 plate=Image.new('RGB',(1000,800),'#bbb');d=ImageDraw.Draw(plate)
 for i,key in enumerate(pair):
  im=Image.open(imgs[key]).convert('RGBA');c=im.crop((930,900,1230,1240));base=Image.new('RGBA',c.size,'#222');base.alpha_composite(c);plate.paste(base.convert('RGB').resize((450,510)),(i*500+25,30));d.text((i*500+10,6),key+' nativecrop spatial1.5x',fill='black')
  sm=im.resize((336,210),Image.Resampling.LANCZOS);base=Image.new('RGBA',sm.size,'#222');base.alpha_composite(sm);plate.paste(base.convert('RGB'),(i*500+60,570))
 plate.save(out/f'own-edge-{pair[0]}-{pair[1]}.png')
(out/'temp.png').unlink()
