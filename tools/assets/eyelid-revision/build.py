#!/usr/bin/env python3
"""Run the native Canvas eye-only compositor; Python transports bytes/records hashes, never edits pixels."""
import base64,json,hashlib,os,zlib,struct,binascii
from PIL import Image
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def raw(p):return base64.b64encode(Image.open(p).convert('RGBA').tobytes()).decode()
def encode_rgba(w,h,rgba):
 def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)
 scan=b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4] for y in range(h))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(scan,7))+chunk(b'IEND',b'')
def data(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'));pg=b.new_page();pg.add_script_tag(path=str(HERE/'build.js'))
 for c in ['fiona','lou']:
  spec=json.loads((HERE/(c+'.json')).read_text());folder=ROOT/f'assets/images/characters/portraits/{c}';inp={'id':c,'normal':data(folder/f'{c}_normal.png'),'normalRaw':raw(folder/f'{c}_normal.png'),'donor':data(HERE/'source'/f'{c}_closed_donor.png'),'eyes':spec['eyes'],'expressions':{}}
  built=pg.evaluate('input=>buildEyeRevision(input)',inp);dest=folder/'provisional-20e';lines=[]
  md=HERE/'masks';md.mkdir(exist_ok=True)
  for eye,encoded in built['allowedMasks'].items():
   box=built['boxes'][eye];(md/f'{c}_{eye}.png').write_bytes(encode_rgba(box[2]-box[0],box[3]-box[1],base64.b64decode(encoded)))
  d=dest/'blink';d.mkdir(parents=True,exist_ok=True)
  for name,encoded in built['patches'].items():
   box=built['boxes'][name.split('_')[1]];ww,hh=box[2]-box[0],box[3]-box[1]
   content=encode_rgba(ww,hh,base64.b64decode(encoded));(d/name).write_bytes(content);lines.append(hashlib.sha256(content).hexdigest()+'  blink/'+name)
  d=dest/'expressions';d.mkdir(parents=True,exist_ok=True);ww,hh=Image.open(folder/f'{c}_normal.png').size
  for face,state in spec['expression_states'].items():
   f=folder/'provisional-20c/expressions'/f'{c}_{face}.png'
   encoded=pg.evaluate('input=>buildEyeExpression(input)',{'state':state,'raw':raw(f)})
   content=encode_rgba(ww,hh,base64.b64decode(encoded));(d/f.name).write_bytes(content);lines.append(hashlib.sha256(content).hexdigest()+'  expressions/'+f.name)
   print(c,face,'built',flush=True)
  (dest/'SHA256SUMS').write_text('\n'.join(lines)+'\n');print(c,len(lines),'assets',built['boxes'],flush=True)
 b.close()
