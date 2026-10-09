from PIL import Image
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[4];src=Path(__file__).with_name('fisherman_animation_sheet.png');im=Image.open(src)
# Visually authored irregular frame regions, not a uniform grid.
frames=[('idle_01',(0,0,320,235)),('idle_02',(320,0,620,235)),('idle_03',(620,0,925,235)),('bite_01',(0,235,335,505)),('reel_01',(335,235,625,505)),('reel_02',(625,235,895,505)),('catch_01',(1410,235,1660,505)),('inspect_01',(1660,235,1900,505)),('inspect_02',(1900,235,2172,505)),('inspect_03',(0,505,215,724)),('inspect_04',(215,505,470,724)),('reset_01',(470,505,720,724))]
rows={}
for key,region in frames:
 frame=im.crop(region);alpha=frame.getchannel('A');core=alpha.point(lambda a:255 if a>=64 else 0)
 # Chair/body/boots ground anchor; exclude the extended rod, bobber and fish.
 body=core.crop((0, min(35,frame.height),min(190,frame.width),frame.height));box=body.getbbox();box=(box[0],box[1]+min(35,frame.height),box[2],box[3]+min(35,frame.height))
 # The grounded figure's horizontal centre is held steady, not the rod's bbox centre.
 ground=core.crop((0,box[3]-25,min(190,frame.width),box[3])).getbbox()
 anchor=[round((ground[0]+ground[2])/2),box[3]]
 name='fisherman_'+key+'.png';frame.save(root/'img/field/lind/npc/fisherman'/name)
 rows[key]={'path':'img/field/lind/npc/fisherman/'+name,'width':frame.width,'height':frame.height,'region':list(region),'anchor':anchor,'bodyBounds':list(box),'visibleBounds':core.getbbox(),'transparentPixels':alpha.histogram()[0],'alphaMinMax':alpha.getextrema(),'edgeCorePixels':sum(core.crop((0,0,frame.width,1)).histogram()[255:])+sum(core.crop((0,frame.height-1,frame.width,frame.height)).histogram()[255:])}
print(json.dumps(rows,indent=2))
(root/'docs/field/qa/lind-village-life-assets/frames.json').write_text(json.dumps(rows,indent=2))
(root/'js/field/lind-fisherman-assets.js').write_text('/* User-provided sheet, individually inspected crops; alpha pixels unchanged. */\nwindow.LindFishermanAssets=Object.freeze('+json.dumps({k:{f:v[f] for f in ['path','width','height','anchor']} for k,v in rows.items()},indent=2)+');\n')
(root/'docs/field/qa/lind-village-life-assets/fisherman_animation_sheet.png').write_bytes(src.read_bytes())
(root/'docs/field/qa/lind-village-life-assets/source.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'size':im.size,'mode':im.mode,'transparentPixels':im.getchannel('A').histogram()[0],'totalPixels':im.width*im.height,'frameLayout':'7 top, 8 middle, 8 bottom; irregular regions','selectedFrames':len(rows),'unused':'Remaining top waits and incomplete bottom reset/rod frames not needed; rightmost bottom rod clipped at source edge'},indent=2))
