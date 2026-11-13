"""Validate shortlist IDs against live provider APIs. Metadata only, no downloads."""
import json,sys,pathlib,urllib.request,urllib.error,datetime
src=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
items=json.loads(src.read_text())['shortlist']
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'THE-WINDBOUND-OATH-AssetResearch/1.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'METADATA_VERIFICATION_ONLY','assets':[]}
for item in items:
 row={**item,'status':'UNVERIFIED','license_check':'PENDING','download':'NOT_PERFORMED'}
 try:
  if item['provider']=='polyhaven':
   data=fetch('https://api.polyhaven.com/info/'+item['asset_id'])
   row['status']='FOUND_TEXTURE' if data.get('type')==1 else 'FOUND_NON_TEXTURE'
   row['provider_type']=data.get('type')
   row['name']=data.get('name')
   row['categories']=data.get('categories')
   row['license_check']='PROVIDER_CC0_POLICY_NEEDS_PER_ASSET_REVIEW'
  elif item['provider']=='ambientcg':
   data=fetch('https://ambientcg.com/api/v3/assets/'+item['asset_id'])
   row['status']='FOUND' if data else 'UNVERIFIED'
   row['license_check']='PROVIDER_CC0_POLICY_NEEDS_PER_ASSET_REVIEW'
 except urllib.error.HTTPError as e:row['status']='HTTP_'+str(e.code)
 except Exception as e:row['status']='ERROR';row['error']=str(e)
 report['assets'].append(row)
dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'statuses':[(a['asset_id'],a['status']) for a in report['assets']]},indent=2))\nif any(a['status'] in ('FOUND_NON_TEXTURE','HTTP_404','ERROR','UNVERIFIED') for a in report['assets']):
 print('WARNING: shortlist contains unresolved entries; do not import or approve')
