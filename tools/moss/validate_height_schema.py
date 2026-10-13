#!/usr/bin/env python3
"""EE: read-only structural checks and production-engine spawn/legacy-coordinate audit."""
import argparse,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def validate(m,s):
 issues=[]
 def err(msg):issues.append(msg)
 def integer(n):return type(n)is int and n>=0
 levels=s.get('levels',{});known=lambda n:integer(n)and(n==0 or str(n)in levels)
 if not isinstance(levels,dict):return ['levels must be an object']
 for k,v in levels.items():
  if not k.isdigit()or str(int(k))!=k:err('invalid level key '+k)
  if not isinstance(v,dict)or not isinstance(v.get('walk'),list):err('missing walk '+k)
 for c in s.get('connectors',[]):
  if not known(c.get('from'))or not known(c.get('to')):err('connector references unknown/noninteger level '+str(c.get('id')))
 for e in s.get('overpasses',[]):
  if not known(e.get('level')):err('overpass unknown/noninteger level '+str(e.get('id')))
 groups={'spawns':list(m.get('spawns',{}).get('points',{}).values())}
 for k in ['transitions','eventZones','treasurePoints','symbols','monsters','walkers']:groups[k]=m.get(k,[])
 for group,entries in groups.items():
  for i,e in enumerate(entries):
   if group=='spawns' and any(type(e.get(axis))not in(int,float)or not math.isfinite(e[axis])for axis in('x','y')):err(f'spawns/{e.get("id",i)} invalid coordinates')
   if 'level'in e and not known(e['level']):err(f'{group}/{e.get("id",i)} invalid level {e["level"]!r}')
   if 'levels'in e and(not isinstance(e['levels'],list)or not e['levels']or not all(known(n)for n in e['levels'])):err(f'{group}/{e.get("id",i)} invalid levels')
 return issues
JS=r'''
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');const root=process.argv[1],data=JSON.parse(fs.readFileSync(0,'utf8')),ctx={performance:require('node:perf_hooks').performance};ctx.window=ctx;vm.createContext(ctx);for(const f of ['field-collision.js','field-height.js'])vm.runInContext(fs.readFileSync(path.join(root,'js/field',f),'utf8'),ctx);
const out=[];for(const {map:m,spec:s,file}of data){const blockers=[...(m.collision?.blockers||[]),...(m.collision?.edgeBlockers||[])],flags=[...new Set(blockers.filter(b=>b.enabledWhen).map(b=>b.enabledWhen.flag))],checks=[],ambiguities=[];if(flags.length>10)throw Error('Too many flags');
for(let mask=0;mask<2**flags.length;mask++){const state=Object.fromEntries(flags.map((f,i)=>[f,!!(mask&(1<<i))])),solid=ctx.FieldCollision.compileMap(blockers,k=>state[k]),h=ctx.FieldHeight.create(s,solid),B=ctx.FieldCollision.footprint,sp=m.spawns?.points||{},start=sp[m.spawns?.default];
 for(const [name,p]of Object.entries(sp)){const x=p.x-B.anchorX,y=p.y-B.anchorY,l=p.level??h.derive(x,y);checks.push({name,kind:'spawn_clear',ok:p.x-11>=0&&p.x+11<=m.world.width&&p.y-10>=0&&p.y<=m.world.height&&!h.blockedAtLevel(x,y,l),level:l,flags:state});if(start){const sx=start.x-B.anchorX,sy=start.y-B.anchorY;h.setLevel(start.level??h.derive(sx,sy));const plan=h.plan({x:sx,y:sy},{x,y,level:l},{width:m.world.width,height:m.world.height,maxNodes:100000});checks.push({name,kind:'spawn_reachable',ok:!!plan.path,level:l,flags:state})}}
 for(const [level,v]of Object.entries(s.levels||{}))if(Number(level)>0)for(const [i,r]of v.walk.entries()){
  const candidates=[[r[0]+r[2]/2,r[1]+r[3]/2],...[.2,.8].flatMap(a=>[.2,.8].map(b=>[r[0]+r[2]*a,r[1]+r[3]*b]))];const examples=[];
  for(const [fx,fy]of candidates){const x=fx-B.anchorX,y=fy-B.anchorY,ls=[0,...Object.keys(s.levels).map(Number).filter(n=>n>0)].filter(l=>!h.blockedAtLevel(x,y,l));if(ls.length>1){h.setLevel(0);const accepted=!h.blocked(x,y),derived=h.derive(x,y);h.setLevel(derived);const effective=h.commit(x,y);examples.push({actor_xy:[x,y],feet:[fx,fy],valid_levels:ls,legacy_precheck_accepts_xy:accepted,legacy_derive:derived,legacy_after_commit:effective})}}
  if(examples.length)ambiguities.push({level:Number(level),rect_index:i,rect:r,flags:state,examples});
 }
}out.push({map:m.id,file,checks,ambiguities})}console.log(JSON.stringify(out));
'''
def self_test():
 m={'spawns':{'points':{'x':{'x':10,'y':10}}}};s={'levels':{'1':{'walk':[[0,0,100,100]]}},'connectors':[]}
 for n in [-1,1.5,True,'1',99]:
  m['spawns']['points']['x']['level']=n
  assert validate(m,s),f'invalid level accepted: {n!r}'
 for n in [0,1]:m['spawns']['points']['x']['level']=n;assert not validate(m,s)
 print('ok   negative/float/bool/string/unknown spawn levels rejected; 0/1 accepted')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.self_test:self_test();return
 data=[];rows=[]
 for f in sorted((ROOT/'data/maps').glob('*.json')):
  m=json.loads(f.read_text());specs=[]
  if m.get('height'):specs.append((str(f.relative_to(ROOT)),m['height']))
  overlay=ROOT/'data/height-specs'/f.name
  if overlay.exists():specs.append((str(overlay.relative_to(ROOT)),json.loads(overlay.read_text())))
  for file,s in specs:
   issues=validate(m,s);rows.append({'file':file,'map':m['id'],'errors':issues})
   if not issues:data.append({'file':file,'map':m,'spec':s})
 actual=json.loads(subprocess.check_output(['node','-e',JS,str(ROOT)],input=json.dumps(data),text=True,timeout=180))
 j={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'schema':rows,'engine':actual,'ambiguity_scope':'all upper walk rectangles; five clear candidate points per rectangle, not exhaustive continuous-world enumeration'}
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
 bad=0
 for row in rows:
  bad+=len(row['errors']);print(('FAIL 'if row['errors']else'ok   ')+row['file']+' '+str(row['errors']))
 for row in actual:
  for c in row['checks']:bad+=not c['ok'];print(('ok   'if c['ok']else'FAIL ')+row['map']+'/'+c['name']+' '+c['kind']+' level='+str(c['level']))
  print('WARN old-save ambiguous rectangles '+row['map']+' '+str(len(row['ambiguities'])))
 print('FAILS',bad);raise SystemExit(bool(bad))
if __name__=='__main__':main()
