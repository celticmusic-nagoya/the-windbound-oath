#!/usr/bin/env python3
"""Verify pinned inventory hashes and protected registrations; refresh GIF alpha metadata."""
import argparse
from pathlib import Path
import hashlib,json,subprocess,sys,io
from collections import Counter
from PIL import Image
from audit_morwen_inventory import blobs, write
parser=argparse.ArgumentParser()
parser.add_argument('--website',required=True)
args=parser.parse_args()
out=Path('docs/qa/morwen-canon-cleanup-01')
x=json.loads((out/'MORWEN_ASSET_INVENTORY.json').read_text()); entries=x['entries']
repositories={'game':'.','website':args.website}
verified=0
for repo,root in repositories.items():
 rows=[e for e in entries if e['repository']==repo]
 data=blobs(root,{e['gitBlob'] for e in rows})
 for e in rows:
  b=data[e['gitBlob']]
  assert hashlib.sha256(b).hexdigest()==e['sha256'],e['path']
  assert len(b)==e['bytes']
  if e['image'] and e['image']['format']=='GIF':
   im=Image.open(io.BytesIO(b))
   a=im.convert('RGBA').getchannel('A').getextrema() if 'A' in im.getbands() or 'transparency' in im.info else None
   e['image']['hasAlpha']=a is not None
   e['image']['alphaRange']=list(a) if a else None
  verified+=1
D=json.loads((out/'DEPENDENCIES.json').read_text())['documents']
assert all(r['document'] in D for e in entries for r in e['references'])
assert x['counts']=={a:sum(e['action']==a for e in entries) for a in ['KEEP','ARCHIVE','DELETE_CANDIDATE','BLOCKED']}
assert len({(e['repository'],e['path'],e['gitBlob']) for e in entries})==len(entries)
assert all(e['action']=='KEEP' for e in entries if e['category'] in ['official_reference','approved_v3','website_asset','portrait_derivative'])
manifest=json.loads(Path('assets/companions/MANIFEST.json').read_text())
# Walk manifest schema without assuming its top-level key.
def objects(z):
 if isinstance(z,dict):
  yield z
  for v in z.values():yield from objects(v)
 elif isinstance(z,list):
  for v in z:yield from objects(v)
expected=[a for a in objects(manifest) if a.get('character')=='morwen' and 'sha256' in a]
assert len(expected)==2
hd=next(s for s in x['snapshots'] if s['ref']=='feature/morwen-hd-canonical-v2-registration')
registry=json.loads(subprocess.check_output(['git','show',hd['commit']+':data/morwen-hd-canonical-v2.json']))
expected+=list(registry['assets'].values())
expected += [dict(path='assets/official/characters/morwen/turnaround/'+f,sha256=h) for f,h in [
 ('file_00000000a6308211aaeeb9e2482c2e83.png','7eeff76ac07f631c14cb536e0e08346cfe815247a88520fb5a68cf0e877e5548'),
 ('file_0000000035a0820989d20c639724cc25.png','d858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591'),
 ('file_00000000055481f8bac7574e5cab00dc.png','9cf2f27448303aa60c603f0f32a7baada234fec8cae5108bf8103a9ae7547e69')]]
for a in expected:
 assert any(e['repository']=='game' and e['path']==a['path'] and e['sha256']==a['sha256'] for e in entries),a['path']
for e in entries:
 if e['repository']=='website' and e['image']:
  p=e['path'].replace('assets/companions/morwen/turnaround/','assets/official/characters/morwen/turnaround/').replace('assets/companions/morwen.webp','web/companions/morwen.webp')
  assert any(g['repository']=='game' and g['path']==p and 'main' in g['snapshots'] and g['sha256']==e['sha256'] for g in entries),e['path']
assert not any(e['sha256']=='47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638' for e in entries)
for s in x['snapshots']:
 if s['repository']=='game':
  name='origin/'+s['ref']
  assert subprocess.check_output(['git','rev-parse',name],text=True).strip()==s['commit']
write('MORWEN_ASSET_INVENTORY.json', x)
summary=dict(entries=verified,registeredHashes=len(expected),websiteImages=sum(e['repository']=='website' and bool(e['image']) for e in entries),counts=x['counts'],mainCounts=dict(Counter(e['action'] for e in entries if e['repository']=='game' and 'main' in e['snapshots'])),duplicateGroups=len(x['duplicateGroups']),snapshots=len(x['snapshots']),documents=len(D))
(out/'QA_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
