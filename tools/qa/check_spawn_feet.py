#!/usr/bin/env python3
"""Read-only all-map audit using the actual FieldCollision/FieldHeight modules in Node."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JS=r'''
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=process.argv[1],ctx={performance:require('node:perf_hooks').performance};ctx.window=ctx;vm.createContext(ctx);
for(const f of ['field-collision.js','field-height.js'])vm.runInContext(fs.readFileSync(path.join(root,'js/field',f),'utf8'),ctx);
const F=ctx.FieldCollision,B=F.footprint,rows=[];if(B.width!==22||B.height!==10)throw Error('Review changed footprint');
const old=F.compileMap([{id:'stool',shape:'rects',rects:[[430.4,436,19.2,14]]}]);
if(!old.blocked(430-B.anchorX,452-B.anchorY)||old.blocked(430-B.anchorX,472-B.anchorY))throw Error('Foot-box negative control failed');
if(process.argv[2]==='self'){console.log(JSON.stringify({self_test:'PASS old stool blocks feet despite free spawn point; corrected position clear'}));process.exit(0)}
for(const file of fs.readdirSync(path.join(root,'data/maps')).filter(f=>f.endsWith('.json')).sort()){
 const m=JSON.parse(fs.readFileSync(path.join(root,'data/maps',file),'utf8'));
 const blockers=[...(m.collision?.edgeBlockers||[]),...(m.collision?.blockers||[])];
 const names=[...new Set(blockers.filter(b=>b.enabledWhen).map(b=>b.enabledWhen.flag))];
 if(names.length>10)throw Error('Too many flag combinations '+file);
 const contexts=Array.from({length:2**names.length},(_,n)=>{
  const flags=Object.fromEntries(names.map((k,i)=>[k,!!(n&(1<<i))]));const solid=F.compileMap(blockers,k=>flags[k]);
  return {flags,solid,h:m.height?ctx.FieldHeight.create(m.height,solid):null};
 });
 for(const [id,s] of Object.entries(m.spawns?.points||{})){
  if(!Number.isFinite(s.x)||!Number.isFinite(s.y))throw Error('Invalid spawn '+file+'/'+id);
  for(const c of contexts){
   const x=s.x-B.anchorX,y=s.y-B.anchorY;let level=0;
   if(c.h){c.h.setLevel(Number.isFinite(s.level)?s.level:c.h.derive(x,y));c.h.commit(x,y);level=c.h.level;}
   const out=s.x-11<0||s.x+11>m.world.width||s.y-10<0||s.y>m.world.height;
   const blocked=out||(c.h?c.h.blockedAtLevel(x,y,level):c.solid.blocked(x,y,0));
   const hits=c.solid.shapes.filter(b=>(!b.enabledWhen||Boolean(c.flags[b.enabledWhen.flag])===Boolean(b.enabledWhen.is))&&(!b.levels||b.levels.includes(level))&&F.overlaps(b,x,y)).map(b=>b.id);
   rows.push({file,map:m.id,scope:m.id.startsWith('dev_')?'DEV':'main',spawn:id,default:m.spawns.default===id,x:s.x,y:s.y,declared_level:s.level??null,effective_level:level,flags:c.flags,clear:!blocked,out_of_bounds:out,blockers:hits});
  }
 }
}
console.log(JSON.stringify({footprint:JSON.parse(JSON.stringify(B)),maps:new Set(rows.map(r=>r.map)).size,main_maps:new Set(rows.filter(r=>r.scope==='main').map(r=>r.map)).size,dev_maps:new Set(rows.filter(r=>r.scope==='DEV').map(r=>r.map)).size,unique_spawns:new Set(rows.map(r=>r.map+'/'+r.spawn)).size,results:rows}));
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 r=subprocess.run(['node','-e',JS,str(ROOT)]+(['self']if a.self_test else []),capture_output=True,text=True,check=True);j=json.loads(r.stdout)
 if a.self_test:print(j['self_test']);return
 j['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(j,ensure_ascii=False,indent=2))
 for row in j['results']:print(('ok   'if row['clear']else 'FAIL ')+f"{row['map']}/{row['spawn']} feet=({row['x']},{row['y']}) level={row['effective_level']} flags={row['flags']} blockers={row['blockers']}")
 bad=sum(not r['clear']for r in j['results']);print('FAILS',bad);raise SystemExit(1 if bad else 0)
if __name__=='__main__':main()
