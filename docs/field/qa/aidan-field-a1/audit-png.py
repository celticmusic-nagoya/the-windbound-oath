"""Read-only PNG validation; visual background/anatomy QA is separate."""
from pathlib import Path
from PIL import Image
import json,hashlib
root=Path(__file__).resolve().parents[4]
rows=json.loads((Path(__file__).parent/'asset-audit.json').read_text())
assert len(rows)==20
assert len(list((root/'img/field/characters/aidan').glob('*.png')))==20
for row in rows:
 p=root/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],p
 im=Image.open(p);im.verify();im=Image.open(p)
 assert im.format=='PNG' and im.mode=='RGBA' and list(im.size)==row['size']
 a=im.getchannel('A');hist=a.histogram();assert hist[0]==row['fullyTransparentPixels'] and hist[0]>0
 b=a.point(lambda n:255 if n>16 else 0).getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<im.width and b[3]<im.height
print('20/20 PNG, SHA, RGBA, alpha0 and visible-edge checks PASS (read only)')
