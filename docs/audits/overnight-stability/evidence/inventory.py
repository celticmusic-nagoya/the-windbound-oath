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
