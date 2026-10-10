from pathlib import Path
from PIL import Image
import numpy as np,hashlib,csv,json,re,collections
root=Path('/workspace/the-windbound-oath');out=Path(__file__).parent
sources=[root/'index.html',*root.glob('js/**/*.js'),*root.glob('css/**/*.css')]
refs=collections.defaultdict(list);dynamic=[]
for f in sources:
 s=f.read_text()
 for m in re.finditer(r'img/[A-Za-z0-9_./ -]+\.(?:png|jpe?g|webp|gif|svg)',s,re.I):refs[m.group()].append(str(f.relative_to(root))+':'+str(s[:m.start()].count('\n')+1))
 for line in s.splitlines():
  if 'img/' in line and ('${' in line or "+'" in line or '+id' in line or '+name' in line):dynamic.append({'source':str(f.relative_to(root)),'expression':line.strip()[:500]})
rows=[];errors=[]
for f in sorted((root/'img').rglob('*')):
 if not f.is_file():continue
 path=str(f.relative_to(root));row={'path':path,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'references':';'.join(refs.get(path,[])),'reference_status':'literal' if path in refs else 'not proven (dynamic or unused)'}
 tags=[]
 for token,tag in [('field','FIELD'),('battle','BATTLE'),('ui','UI'),('cutin','CUT-IN'),('characters','CHARACTER'),('npc','NPC'),('enemies','ENEMY'),('effect','EFFECT'),('landmark','LANDMARK'),('terrain','TERRAIN'),('building','BUILDING')]:
  if token in path.lower().split('/') or (token=='building' and '/buildings/' in path) or (token=='cutin' and 'cutin' in f.name.lower()) or (token=='effect' and '/environment/' in path):tags.append(tag)
 row['category']=';'.join(tags) or 'OTHER'
 try:
  im=Image.open(f);row.update(width=im.width,height=im.height,format=im.format,mode=im.mode,alpha='A' in im.getbands() or 'transparency' in im.info,decoded_rgba_bytes=im.width*im.height*4)
  if row['alpha']:
   a=np.array(im.convert('RGBA').getchannel('A'));row['transparent_pct']=float((a==0).mean()*100);row['partial_alpha_pct']=float(((a>0)&(a<255)).mean()*100)
  else:row.update(transparent_pct=0,partial_alpha_pct=0)
  row['flags']=';'.join([x for test,x in [(row['bytes']>2*1024**2,'bytes>2MiB'),(max(im.size)>2048,'axis>2048'),(min(im.size)<64,'axis<64')] if test])
 except Exception as e:row.update(format=f.suffix,flags='not raster / inspect manually');errors.append({'path':path,'message':str(e)})
 rows.append(row)
index={r['path'].lower():r['path'] for r in rows};missing=[]
for ref,places in refs.items():
 if not (root/ref).is_file():missing.append({'path':ref,'sources':places,'case_match':index.get(ref.lower())})
dups=collections.defaultdict(list)
for r in rows:dups[r['sha256']].append(r['path'])
fields=sorted(set().union(*(r.keys() for r in rows)))
with (out/'asset-inventory.csv').open('w') as f:
 w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(rows)
result={'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'decoded_rgba_bytes':sum(r.get('decoded_rgba_bytes',0) for r in rows),'category_counts':dict(collections.Counter(r['category'] for r in rows)),'missing_literal':missing,'dynamic_expressions':dynamic,'exact_duplicates':[v for v in dups.values() if len(v)>1],'non_raster_or_errors':errors,'legacy_references':{term:sum(len(re.findall(term,f.read_text())) for f in sources) for term in [r'battle/embedded',r'asset_\d+_',r'battle/support/lou']},'embedded_exists':(root/'img/battle/embedded').exists()}
(out/'inventory-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['dynamic_expressions','exact_duplicates']},ensure_ascii=False))

# Optional runtime evidence enriches provenance; registration is not visible use.
runtime=set(json.loads((out/'runtime-references.json').read_text())) if (out/'runtime-references.json').exists() else set()
pairs=[]
for row in rows:
 row['runtime_or_registry_seen']=row['path'] in runtime
 row['reference_status']='runtime request or runtime registry' if row['path'] in runtime else 'literal metadata/reference; visible use not established' if row['references'] else 'unreferenced in audited source/runtime; retained'
 row['visual_review']='contact sheet: no obvious baked matte at thumbnail scale'
 if row.get('transparent_pct')==0:row['visual_review']='opaque terrain tile: intentional' if '/terrain/' in row['path'] else 'white/light background visually baked; no edits'
 if 'reference_sheet' in row['path']:row['visual_review']='design reference composite, not production sprite'
 if '/landmarks/' in row['path']:row['category']+=';LANDMARK'
 im=Image.open(root/row['path']).convert('RGBA');bg=Image.new('RGBA',im.size,(76,94,91,255));bg.alpha_composite(im);v=np.asarray(bg.convert('L').resize((9,8)));bits=(v[:,:-1]>v[:,1:]).flatten();value=0
 for bit in bits:value=(value<<1)|int(bit)
 row['dhash64']=f'{value:016x}'
for i,a in enumerate(rows):
 for b in rows[i+1:]:
  distance=(int(a['dhash64'],16)^int(b['dhash64'],16)).bit_count()
  if distance<=3:pairs.append({'a':a['path'],'b':b['path'],'hash_distance':distance,'note':'visual-similarity screening only; state frames intentionally similar, not deletion advice'})
for row in rows:row['duplicate_candidates']=';'.join(pair['b'] if pair['a']==row['path'] else pair['a'] for pair in pairs if row['path'] in [pair['a'],pair['b']])
with (out/'asset-inventory.csv').open('w') as f:
 w=csv.DictWriter(f,sorted(set().union(*(r.keys() for r in rows))),lineterminator='\n');w.writeheader();w.writerows(rows)
(out/'similarity-candidates.json').write_text(json.dumps(pairs,indent=2))
result.update(runtime_registry_or_requests=len(runtime),missing_runtime_or_registry=[x for x in runtime if not (root/x).is_file()],retained_unreferenced=[r['path'] for r in rows if r['reference_status'].startswith('unreferenced')],rgba=sum(r['mode']=='RGBA' for r in rows),rgb=sum(r['mode']=='RGB' for r in rows),perceptual_candidate_pairs=len(pairs),category_counts=dict(collections.Counter(r['category'] for r in rows)))
(out/'inventory-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
