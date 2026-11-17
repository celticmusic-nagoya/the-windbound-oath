"""Scoped technical QA and visual-review aids. Does not approve character art."""
import json,pathlib,sys,hashlib
from PIL import Image,ImageDraw
import numpy as np
root=pathlib.Path(sys.argv[1]);ev=json.loads((root/'render_evidence.json').read_text());rows=[]
for v in ev['views']:
 im=Image.open(root/v['file']);a=np.asarray(im.convert('RGBA'));mask=a[:,:,3]>16;colors=a[:,:,:3][mask];n=int(mask.sum())
 clip=float(np.mean(np.all(colors>=250,axis=1))) if n else 1;crush=float(np.mean(np.all(colors<=5,axis=1))) if n else 1
 passed=im.mode=='RGBA' and n>500 and clip<.01 and crush<.05 and v['head_framed']
 rows.append({'file':v['file'],'mode':im.mode,'size':im.size,'visible_pixels':n,'white_clip_fraction':clip,'black_crush_fraction':crush,'head_framed':v['head_framed'],'pass':passed})
 if v['mode']=='color':
  for size in [64,128]:im.resize((size,size),Image.Resampling.LANCZOS).save(root/(v['view']+'_'+str(size)+'px.png'))
checks={'source_unchanged':ev['source_unchanged'],'reopen':ev['reopen_pass'],'canonical_packed_bytes':ev['references_verified'],'new_face_geometry':ev['face_changed_vertices']>0,'closed_nondegenerate_evaluated_meshes':all(not m['nonmanifold_edges'] and not m['degenerate_faces'] for m in ev['meshes']),'finite_and_outward_volume':all(m['finite_coordinates'] and m['signed_volume']>0 for m in ev['meshes']),'rgba_visibility_frame':all(r['pass'] for r in rows),'twelve_color_clay_views':len(rows)==12,'anatomical_ratio':7.5<=ev['head_count']<=8}
report={'status':'PASS_TECHNICAL_SCREEN' if all(checks.values()) else 'FAIL_TECHNICAL_SCREEN','checks':checks,'renders':rows,'G1':'BLOCKED_PROVISIONAL_REFERENCE_REGISTRATION','G2':'NOT_APPROVED; independent new-candidate visual QA NOT_RUN; self findings in report','G3':'PASS_TECHNICAL_SCREEN' if all(checks.values()) else 'FAIL','G4':'NOT_RUN','limitations':['No self-intersection or lens/skin support certification','No facial rig/deformation/UV/game or actual Android test','Projected bounds exclude intentionally cropped shoulders','Two-point hair-crown proxy does not establish anatomical image calibration']}
(root/'technical_qa.json').write_text(json.dumps(report,indent=2)+'\n')
for mode in ['color','clay']:
 sheet=Image.new('RGB',(1152,832),(42,43,49));draw=ImageDraw.Draw(sheet)
 for i,v in enumerate([v for v in ev['views'] if v['mode']==mode]):
  im=Image.open(root/v['file']).convert('RGBA');bg=Image.new('RGBA',im.size,(42,43,49,255));bg.alpha_composite(im);bg=bg.convert('RGB').resize((384,384),Image.Resampling.LANCZOS)
  x=(i%3)*384;y=(i//3)*416;sheet.paste(bg,(x,y+24));draw.text((x+10,y+7),v['view'],fill='white')
 sheet.save(root/(mode+'_contact_sheet.png'))
# Accurate reference-to-camera affine registration preserving source pixel aspect.
# This is a diagnostic overlay using the declared proxy anchors, NOT a verified target silhouette.
import math
reg=json.loads(pathlib.Path('docs/qa/morwen-sculpt02/reference_registration.json').read_text())['views']
# Extract exact packed images with bpy only in the render step; QA uses byte-preserved exported originals.
for label,view_name in [('front','front'),('profile','character_left')]:
 original=root/reg[label]['file']
 if not original.exists():continue
 ref=Image.open(original).convert('RGBA');v=next(v for v in ev['views'] if v['mode']=='color' and v['view']==view_name)
 rx,ry,rz=v['rotation'];cx,sx=math.cos(rx),math.sin(rx);cy,sy=math.cos(ry),math.sin(ry);cz,sz=math.cos(rz),math.sin(rz)
 rot=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
 right=rot[:,0];up=rot[:,1];cam=np.array(v['camera']);scale=reg[label]['world_units_per_pixel'];ax,ay=reg[label]['chin_px']
 ch=json.loads(pathlib.Path('docs/qa/morwen-sculpt02/geometry_difference.json').read_text())['chin'];ch=np.array(ch)
 # Pixel chin matches world chin (front x=0 convention differs by only 0.02 mm).
 px=384+np.dot(ch-cam,right)*768/v['ortho_scale'];py=384-np.dot(ch-cam,up)*768/v['ortho_scale'];factor=scale*768/v['ortho_scale']
 transformed=ref.transform((768,768),Image.Transform.AFFINE,(1/factor,0,ax-px/factor,0,1/factor,ay-py/factor),Image.Resampling.BICUBIC)
 base=Image.open(root/('color_'+view_name+'.png')).convert('RGBA');bg=Image.new('RGBA',base.size,(42,43,49,255));bg.alpha_composite(base)
 alpha=transformed.getchannel('A').point(lambda a:int(a*.3));transformed.putalpha(alpha);bg.alpha_composite(transformed)
 ImageDraw.Draw(bg).text((12,12),'PROVISIONAL chin + visible hair-crown overlay; G1 BLOCKED',fill='white');bg.save(root/('reference_overlay_'+label+'.png'))
# Hash all current payload; do not hash the manifest into itself.
files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(root/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in files))
print(json.dumps({'status':report['status'],'checks':checks}))
if not all(checks.values()):sys.exit(2)
