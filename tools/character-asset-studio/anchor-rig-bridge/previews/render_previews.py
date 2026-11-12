from pathlib import Path
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
import json,hashlib
from PIL import Image
base=Path('tools/character-asset-studio/anchor-rig-bridge').resolve();sources=list((base/'measurements/inputs').glob('*.svg'))+list((base/'previews').glob('SYNTHETIC_*.svg'));rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium')
 for src in sources:
  r=ET.parse(src).getroot()
  for e in r.iter():
   assert e.tag.split('}')[-1] not in ('script','foreignObject','image','use')
   assert not any(k.startswith('on') for k in e.attrib)
  width,height=int(r.get('width')),int(r.get('height'))
  page=b.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  page.route('**/*',lambda route:route.abort())
  page.set_content('<style>body{margin:0}</style>'+src.read_text())
  out=base/'previews'/(src.stem+'.png');page.locator('svg').screenshot(path=str(out),omit_background=True);page.close()
  with Image.open(out) as im:
   assert im.size==(width,height) and im.mode=='RGBA'
   hist=im.getchannel('A').histogram()
   rows.append({'path':str(out.relative_to(base)),'source':str(src.relative_to(base)),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'size':list(im.size),'mode':im.mode,'transparentPixels':hist[0],'status':'PASS' if hist[0]>0 else 'FAIL','classification':'DERIVED_PREVIEW_NOT_NATIVE_SOURCE_PNG'})
 b.close()
(base/'qa/png_previews.json').write_text(json.dumps({'nativeSourcePngQA':'NOT_RUN (attachments contain SVG, not PNG)','rows':rows},indent=2)+'\n')
print('Derived PNG previews verified',len(rows))
