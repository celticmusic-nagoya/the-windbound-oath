from PIL import Image,ImageDraw
from pathlib import Path
import subprocess,json
OUT=Path(__file__).parent
VIDEO=OUT.parent/'attempt3-pc-four-conditions.webm'
starts={'A':12.05,'B':29.55,'C':47.85,'D':66.25}
rows=[]
for label,start in starts.items():
 frames=[]
 for n in range(12):
  f=OUT/f'actual-{label}-{n:02}.png'
  subprocess.run(['ffmpeg','-v','error','-ss',str(start+n*.08),'-i',str(VIDEO),'-frames:v','1','-y',str(f)],check=True)
  frames.append(Image.open(f).convert('RGB').crop((205,90,280,220)))
 plate=Image.new('RGB',(75*12,154),'#ddd');d=ImageDraw.Draw(plate)
 for n,im in enumerate(frames):plate.paste(im,(75*n,24));d.text((75*n+2,3),f'{label}+{n*.08:.2f}',fill='black')
 rows.append(plate)
plate=Image.new('RGB',(900,154*4),'white')
for i,row in enumerate(rows):plate.paste(row,(0,154*i))
plate.save(OUT/'own-actual-straight-chronology.png')
# Four simultaneously replayed same-spatial crop, no temporal rate change. Enlarging uses nearest only.
for label,start in starts.items():
 subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-i',str(VIDEO),'-t','0.9','-vf',f'crop=76:130:205:90,drawtext=text={label}:x=2:y=2:fontsize=12:fontcolor=white','-an','-c:v','libx264','-pix_fmt','yuv420p','-y',str(OUT/f'clip-{label}.mp4')],check=True)
args=['ffmpeg','-v','error']
for label in starts:args+=['-i',str(OUT/f'clip-{label}.mp4')]
args+=['-filter_complex','[0:v][1:v][2:v][3:v]hstack=inputs=4[v]','-map','[v]','-an','-y',str(OUT/'own-actual-ABCD-1x.mp4')]
subprocess.run(args,check=True)
subprocess.run(['ffmpeg','-v','error','-i',str(OUT/'own-actual-ABCD-1x.mp4'),'-vf','scale=1216:520:flags=neighbor','-an','-y',str(OUT/'own-actual-ABCD-1x-enlarged.mp4')],check=True)
(OUT/'capture-seeks.json').write_text(json.dumps({'source':str(VIDEO),'source_resolution':[640,360],'source_temporal_fps':25,'starts_seconds':starts,'duration':.9,'rate':1,'crop':[205,90,75,130],'note':'Source video is PC 1920x1080 downsampled to640x360; enlargement spatial only. Fixed common crop, no body registration.'},indent=2))
