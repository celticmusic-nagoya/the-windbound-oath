import json,hashlib,re,subprocess,collections,pathlib
R=pathlib.Path(__file__).resolve().parents[4]; O=pathlib.Path(__file__).resolve().parent;maps=[];trans=[];audio=[]
for p in sorted((R/'data/maps').glob('*.json')):
 d=json.loads(p.read_text());maps.append({'id':d.get('id',p.stem),'world':d.get('world'),'spawns':list(d.get('spawns',{})),'events':[{'id':z.get('id'),'hook':z.get('hook'),'eventId':z.get('eventId')} for z in d.get('eventZones',[])],'treasures':[t.get('id') for t in d.get('treasurePoints',[])]})
 for t in d.get('transitions',[]):trans.append({'from':d.get('id',p.stem),**t})
 audio.append({'map':d.get('id',p.stem),'audio':d.get('audio')})
locked={}
for name in ['PHASE4_ADOPTED_SHA256SUMS','PHASE4_EXPRESSION_BLINK_ADOPTED_SHA256SUMS','PHASE4_FIONA_22BR4_SHA256SUMS']:
 for line in (R/'docs/portraits'/name).read_text().splitlines():
  h,f=line.split(maxsplit=1);locked[f]=h
for a in json.loads((R/'docs/portraits/PHASE4_FORMAL_ADOPTION_21A.json').read_text())['other_protected_pngs']:locked[a['file']]=a['sha256']
protected=[{'file':f,'expected':h,'actual':hashlib.sha256((R/f).read_bytes()).hexdigest()} for f,h in sorted(locked.items())]
registry=json.loads((R/'docs/assets/ASSET_REGISTRY.json').read_text())
files=subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines()
runtime=[f for f in files if f=='index.html' or f.startswith(('js/','css/','data/','img/','assets/','dev/'))]
manifest=''.join(hashlib.sha256((R/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in runtime if (R/f).is_file())
(O/'runtime-SHA256SUMS').write_text(manifest)
v={'base':subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),'map_count':len(maps),'maps':maps,'transitions':trans,'audio':audio,'registry_summary':registry['summary'],'protected_pngs':protected,'protected_count':len(protected),'protected_pass':all(a['actual']==a['expected'] for a in protected),'runtime_files':len(manifest.splitlines()),'runtime_manifest_sha256':hashlib.sha256(manifest.encode()).hexdigest(),'fixture_diagnostics':{'baseline':'12 suites PASS / 2 suites FAIL','in_memory_adapter_only':'startup20 / continue37 PASS; original files unchanged'}}
(O/'static-inventory.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v[k] for k in ['map_count','protected_count','protected_pass','runtime_files','runtime_manifest_sha256']}));print('TBD transitions',[(t['from'],t['id'],t.get('note')) for t in trans if t.get('toMap')=='TBD'])
