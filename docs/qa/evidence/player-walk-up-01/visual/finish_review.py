from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,math,statistics,gzip
p=Path(__file__).parent
video=p.parent/'attempt3-pc-four-conditions.webm'
times={'A':[12.05,17.02,21.50],'B':[29.55,34.43,38.95],'C':[47.85,52.76,57.25],'D':[66.25,71.18,75.70]}
plate=Image.new('RGB',(640,4*3*130),'white');dr=ImageDraw.Draw(plate)
for mi,(mode,starts) in enumerate(times.items()):
 for route,start in enumerate(starts):
  y=(mi*3+route)*130;dr.text((2,y),f'{mode} '+['UP','UL','UR'][route]+' | +0.08 / +0.40 / +0.72 sec; temporal chronology, full scene',fill='black')
  for n,dt in enumerate([.08,.4,.72]):
   f=p/'temp-frame.png';subprocess.run(['ffmpeg','-v','error','-ss',str(start+dt),'-i',str(video),'-frames:v','1','-y',str(f)],check=True)
   plate.paste(Image.open(f).convert('RGB').resize((213,120)),(n*213,y+10))
plate.save(p/'own-actual-allroutes-chronology.png');(p/'temp-frame.png').unlink()
d=json.load(gzip.open(p.parent/'screens/up-runs.json.gz','rt'));metrics=[]
for r in d:
 if r.get('kind')!='field':continue
 rows=r['rows'];speeds=[]
 for a,b in zip(rows,rows[1:]):
  dt=(b['t']-a['t'])/1000
  if dt>0:
   try: dist=math.hypot(b['x']-a['x'],b['y']-a['y'])
   except KeyError:continue
   if dist>0:speeds.append(dist/dt)
 metrics.append({'mode':r['mode'],'route':r.get('route'), 'moving_speed_median':statistics.median(speeds) if speeds else None,'sample_count':len(speeds),'note':'Observational parent telemetry; not independent browser run or proof of support-foot friction'})
(p/'own-route-metrics.json').write_text(json.dumps(metrics,indent=2))
