"""Extract chronological actual browser-video frames for image inspection; no browser/source edits."""
import argparse,json,subprocess
from pathlib import Path
from fractions import Fraction
from PIL import Image,ImageDraw
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--video',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--clips',nargs='+',default=['A=14.0','B=16.3','C=18.9']);p.add_argument('--duration',type=float,default=1);p.add_argument('--crop',nargs=4,type=int,default=[117,218,185,289]);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate','-of','json',str(a.video)],text=True))['streams'][0];fps=float(Fraction(meta['r_frame_rate']))
rows=[]
for pair in a.clips:
 mode,t=pair.split('=');dest=a.out/('actual-field-'+mode);dest.mkdir(exist_ok=True)
 subprocess.run(['ffmpeg','-v','error','-y','-ss',t,'-i',str(a.video),'-t',str(a.duration),'-fps_mode','passthrough',str(dest/'f%03d.png')],check=True)
 paths=sorted(dest.glob('f*.png'));rows.append((mode,float(t),paths));Image.open(paths[0]).save(a.out/f'actual-field-{mode}-first.png')
w=a.crop[2]-a.crop[0];h=a.crop[3]-a.crop[1];plate=Image.new('RGB',(50+max(len(z) for _,_,z in rows)*w,len(rows)*(h+39)),(40,40,40));d=ImageDraw.Draw(plate)
for r,(mode,t,ps) in enumerate(rows):
 y=r*(h+39);d.text((3,y+45),mode,fill='white')
 for i,p in enumerate(ps):
  q=Image.open(p).crop(a.crop);plate.paste(q,(50+i*w,y+25));d.text((50+i*w+1,y+5),f'+{round(i/fps*1000)}ms',fill='white')
plate.save(a.out/'actual-field-ABC-chronological.png');(a.out/'actual-video-inspection.json').write_text(json.dumps({'source_video':str(a.video),'video_metadata':meta,'duration_per_clip':a.duration,'crop_video_px':a.crop,'clip_start_seconds':{m:t for m,t,_ in rows},'decoded_frame_counts':{m:len(ps) for m,_,ps in rows},'limits':'Timeordered decodedparentcaptureframes, not ownbrowseror actualAndroid. Relativeframe labels use nominalvideofps; root actualtelemetry establishes sourcecadence.'},indent=2))
