"""Read-only CC0 candidate discovery; no source files downloaded or approved."""
import json,urllib.request,urllib.parse,pathlib,sys,datetime
out=pathlib.Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
UA='THE-WINDBOUND-OATH-AssetResearch/1.0'
terms={'stone':['stone wall','limestone'],'timber':['wood planks','old wood'],'roof':['thatch','straw'],'ground':['dirt ground','cobblestone']}
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=25) as resp:return json.load(resp)
report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'RESEARCH_ONLY','license_policy':'verify exact asset and terms before download or import','credit':'Powered by Poly Haven (live API discovery)','sources':{},'candidates':[],'errors':[]}
try:
 catalog=get('https://api.polyhaven.com/assets?type=textures')
 report['sources']['polyhaven']={'api':'https://api.polyhaven.com/assets?type=textures','items':len(catalog),'license':'CC0 per provider'}
 for group,words in terms.items():
  matches=[]
  for ident,meta in catalog.items():
   hay=' '.join([str(meta.get('name','')),str(meta.get('description','')),' '.join(meta.get('tags',[]))]).lower()
   score=sum(2 if w in hay else sum(1 for t in w.split() if t in hay) for w in words)
   if score:matches.append((score,ident,meta))
  for score,ident,meta in sorted(matches,key=lambda x:(-x[0],x[1]))[:5]:
   report['candidates'].append({'source':'polyhaven','category':group,'id':ident,'name':meta.get('name'),'score':score,'asset_page':'https://polyhaven.com/a/'+ident,'status':'unreviewed_candidate'})
except Exception as exc:report['errors'].append({'source':'polyhaven','error':str(exc)})
for group,words in terms.items():
 try:
  query=urllib.parse.urlencode({'type':'material','q':words[0],'limit':5,'include':'title,tags,downloads'})
  data=get('https://ambientcg.com/api/v3/assets?'+query)
  report['sources']['ambientcg']={'api':'https://ambientcg.com/api/v3/assets','license':'CC0 per provider'}
  for asset in data.get('assets',[]):
   report['candidates'].append({'source':'ambientcg','category':group,'id':asset.get('id'),'name':asset.get('title'),'asset_page':'https://ambientcg.com/a/'+str(asset.get('id')),'status':'unreviewed_candidate'})
 except Exception as exc:report['errors'].append({'source':'ambientcg','category':group,'error':str(exc)})
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Candidates:',len(report['candidates']),'Errors:',len(report['errors']))
if not report['candidates']:raise SystemExit('No candidates; discovery blocked')
