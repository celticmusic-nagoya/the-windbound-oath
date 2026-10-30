"""20E: raw-RGBA eye-mask integrity, source/protected hashes and immutable revision provenance."""
import json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];ledger=json.loads((ROOT/'docs/portraits/PHASE4_EYELID_REVISION_20E.json').read_text());fails=[]
def check(ok,name):
 print(('ok   ' if ok else 'FAIL ')+name,flush=True)
 if not ok:fails.append(name)
check(len(ledger['assets'])==28 and sum(a['kind']=='blink' for a in ledger['assets'])==16,'exact16 blink overlays +12 expression revisions')
check(all(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] and a['adoption_status']=='PROVISIONAL_ANDROID_QA' for a in ledger['assets']),'all28 revision SHA/status exact')
check(len(ledger['protected_assets'])==110 and all(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in ledger['protected_assets']),'all110 existing PNGs unchanged incl67 adopted+43previous candidates; Emma excluded')
for c in ['fiona','lou']:
 cfg=json.loads((ROOT/f'tools/assets/eyelid-revision/{c}.json').read_text());folder=ROOT/f'assets/images/characters/portraits/{c}';size=Image.open(folder/f'{c}_normal.png').size
 allowed=bytearray(size[0]*size[1])
 for e,E in cfg['eyes'].items():
  x0,y0,x1,y1=E['box'];m=Image.open(ROOT/f'tools/assets/eyelid-revision/masks/{c}_{e}.png').convert('L');check(m.size==(x1-x0,y1-y0),c+' '+e+': explicit mask dimensions')
  v=m.tobytes()
  for y in range(y0,y1):
   for x in range(x0,x1):
    if v[(y-y0)*(x1-x0)+x-x0]:allowed[y*size[0]+x]=1
 for a in [a for a in ledger['assets'] if a['character']==c]:
  new=Image.open(ROOT/a['file']).convert('RGBA')
  if a['kind']=='expression':
   old=Image.open(folder/'provisional-20c/expressions'/Path(a['file']).name).convert('RGBA');nb=new.tobytes();ob=old.tobytes()
   check(new.size==old.size and nb[3::4]==ob[3::4],c+' '+a['expression']+': exact original size and EVERY alpha byte')
   check(all(allowed[i] or nb[4*i:4*i+4]==ob[4*i:4*i+4] for i in range(len(allowed))),c+' '+a['expression']+': every RGBA pixel outside eye masks EXACT')
  else:
   e=Path(a['file']).stem.split('_')[1];E=cfg['eyes'][e];box=E['box'];check(new.size==(box[2]-box[0],box[3]-box[1]) and set(new.getchannel('A').tobytes())<={0,255},c+' '+Path(a['file']).stem+': binary overlay alpha/source-sized coordinates')
# Visual defects caught by independent review: no future closed-lash stripe in the partial frame,
# and no old upper-lash spikes above Lou's closed eyes. These checks fail on the first20E build.
f=Image.open(ROOT/'assets/images/characters/portraits/fiona/provisional-20e/blink/normal_L_s3.png').convert('RGBA')
check(all(f.getpixel((x-508,y-298))[1]>150 for x,y in [(534,339),(537,339)]),'Fiona partial frame has skin instead of a second closed-lash contour')
normal=Image.open(ROOT/'assets/images/characters/portraits/lou/lou_normal.png').convert('RGBA')
for state in range(1,5):
 im=Image.open(ROOT/f'assets/images/characters/portraits/lou/provisional-20e/blink/normal_L_s{state}.png').convert('RGBA')
 check(all(im.getpixel((x-678,y-354))[3]==255 and im.getpixel((x-678,y-354))[1]>normal.getpixel((x,y))[1]+25 for x,y in [(716,362),(731,360),(722,358),(733,371),(716,371)]),f'Lou frame{state}: old upper-lash spikes removed inside narrow masks')
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
