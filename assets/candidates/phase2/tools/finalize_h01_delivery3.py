from PIL import Image,ImageDraw,ImageFilter
import numpy as np, os, cv2, json
src='/mnt/data/d3inspect/h01_fix/repaired'; out='/mnt/data/h01_delivery3_final';os.makedirs(out,exist_ok=True)
for n in ['chair_back','jar','stool','table_small']:
 im=Image.open(f'{src}/furn_h01_{n}.png').convert('RGBA');a=np.array(im)
 if n=='jar':
  # remove isolated bright gray/white spill below jar edge at bottom right
  for y in range(89,104):
   for x in range(80):
    r,g,b,al=a[y,x]
    if al and (int(r)+int(g)+int(b)>550 and max(r,g,b)-min(r,g,b)<45):a[y,x]=[0,0,0,0]
  # remove stray light pixels on right edge of foot, keeping central ceramic foot
  for y in range(98,104):
   for x in range(58,80):
    if a[y,x,3] and a[y,x,:3].min()>145:a[y,x]=[0,0,0,0]
 if n=='chair_back':
  # clear thin disconnected line under seat, preserving supporting rails
  for y in range(77,89):
   for x in range(25,55):
    r,g,b,al=a[y,x]
    if al and abs(int(r)-int(g))<14 and abs(int(g)-int(b))<14 and r>95:a[y,x]=[0,0,0,0]
 if n=='table_small':
  # remove neutral gray residual pixels in the open gap between legs
  for y in range(100,144):
   for x in range(48,145):
    r,g,b,al=a[y,x]
    if al and max(r,g,b)-min(r,g,b)<20 and r>90:a[y,x]=[0,0,0,0]
 if n=='stool':
  # Rebuild missing stool seat as a solid wooden oval with a subtly upholstered inset.
  # retain original carved legs and brace, overlay seat at original intended top.
  im=Image.fromarray(a,'RGBA'); d=ImageDraw.Draw(im)
  d.ellipse((4,7,61,31),fill=(62,32,15,255),outline=(39,23,14,255),width=2)
  d.ellipse((6,8,59,27),fill=(143,82,39,255),outline=(205,137,64,255),width=2)
  d.ellipse((9,7,56,23),fill=(68,103,55,255),outline=(41,63,34,255),width=2)
  d.arc((12,8,54,20),185,345,fill=(139,163,84,255),width=2)
  for x in [12,21,31,41,51]:d.ellipse((x,25,x+2,27),fill=(217,158,71,255))
  a=np.array(im)
 # binary alpha and no transparent RGB
 a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0,:3]=0
 Image.fromarray(a,'RGBA').save(f'{out}/furn_h01_{n}.png')
 # numeric QA
 z=np.array(Image.open(f'{out}/furn_h01_{n}.png')); assert set(np.unique(z[:,:,3])).issubset({0,255}) and not z[z[:,:,3]==0,:3].any()
 print(n,z.shape,'bottom',bool(z[-1,:,3].any()))
with open(f'{out}/QA_NOTES.md','w') as f:f.write('# Delivery 3 revised candidates\n\nLocal numeric QA: RGBA, dimensions, binary alpha, transparent RGB zero PASS.\n\nStool seat reconstructed; jar/chair/table neutral spill cleanup. Visual and in-game acceptance QA pending. Not formally approved.\n')
