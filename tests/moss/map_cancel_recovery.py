"""Commit-complete cancellation is distinct from partial/failed commit."""
from map_recovery_support import *
s=Suite('map-cancel-recovery')
def cancel(p,ck,action):
 p.evaluate('()=>{window.calls=0;window.village=RildeVillage;window.RildeVillage={...village,onEnter(...a){calls++;return village.onEnter(...a)}};window.pending=MossForest.enter({map:"'+B+'",transition:"slow"}).then(x=>!!x)}')
 p.wait_for_function('MossForest.mapRequest.phase==="fading-in"',timeout=15000);p.evaluate(action)
 ck(p.evaluate('pending') is False,'cancelled continuation returns null');ck(not state(p)['unsafe'],'complete and consistent cancel releases latch');ck(p.evaluate('calls===1'),'onEnter completed once, no lost/double hook')
 if action=='MossForest.lock(true)':ck(state(p)['busy'],'external lock retained')
 if action=='MossForest.hide()':ck(not state(p)['active'],'hide remains hidden')
 p.evaluate('MossForest.lock(false);MossForest.resume()');ck(state(p)['active'] and not state(p)['busy'] and state(p)['save'],'normal unlock/resume returns input and save')
 before=state(p);p.evaluate('MossForest.cancelMapRequest();MossForest.lock(false)');ck(not state(p)['unsafe'] and state(p)['feet']==before['feet'],'repeated cancel/unlock is idempotent')
def mismatch(p,ck,field='width'):
 p.evaluate('()=>{window.pending=MossForest.enter({map:"'+B+'",transition:"slow"}).then(x=>!!x)}');p.wait_for_function('MossForest.mapRequest.phase==="fading-in"');p.evaluate('MossForest.map.world.width++;MossForest.hide();MossForest.resume();MossForest.lock(false)' if field=='width' else 'MossForest.map.id="wrong-map-id";MossForest.hide();MossForest.resume();MossForest.lock(false)');assert_stopped(p,ck,'changed commit certificate');ck(p.evaluate('pending') is False,'mismatched cancelled continuation rejected')
def prepare_cancel(p,ck):
 old=state(p);p.evaluate('()=>{window.base=ForestLoader;window.release=null;window.ForestLoader={...base,prepare:async(...a)=>{await new Promise(r=>release=r);return base.prepare(...a)}};window.pending=MossForest.enter({map:"'+B+'"}).then(x=>!!x)}');p.wait_for_function('!!release');p.evaluate('MossForest.hide();MossForest.resume();release()');ck(p.evaluate('pending') is False,'precommit cancellation rejected');ck(state(p)['map']==old['map'] and not state(p)['unsafe'] and state(p)['active'],'precommit retains last valid map')
def notify_error(p,ck):
 p.evaluate('()=>{window.village=RildeVillage;window.RildeVillage={...village,onEnter(){throw Error("cancel-hook-failed")}};window.pending=MossForest.enter({map:"'+B+'",transition:"slow"}).then(x=>!!x)}');p.wait_for_function('MossForest.mapRequest.phase==="fading-in"');p.evaluate('MossForest.hide();MossForest.resume();MossForest.lock(false)');assert_stopped(p,ck,'cancel hook failure');ck(p.evaluate('pending') is False,'failed hook old continuation rejected')
def reentry(p,ck):
 p.evaluate('()=>{window.village=RildeVillage;window.RildeVillage={...village,onEnter(m){if(m.id==="'+B+'")window.next=MossForest.enter({map:"'+A+'"})}};window.pending=MossForest.enter({map:"'+B+'",transition:"slow"})}');p.wait_for_function('MossForest.mapRequest.phase==="fading-in"');p.evaluate('MossForest.cancelMapRequest()');p.wait_for_function('MossForest.mapId==="'+A+'"&&MossForest.active&&!MossForest.busy',timeout=15000);ck(p.evaluate('MossForest.mapRequest.phase==="ready"'),'cancel hook reentry cannot revoke successor')
def after_failed_load(p,ck):
 save(p);fail_map(p);p.evaluate('window.bad=JSON.parse(localStorage.getItem(SAVE_KEY));bad.prologue.version=99;localStorage.setItem(SAVE_KEY,JSON.stringify(bad));renderSystemTab("save")')
 ck(p.evaluate('loadGrowthData()') is False,'prior LOAD failed');assert_stopped(p,ck,'prior LOAD failure')
 cancel(p,ck,'MossForest.hide()');ck(not state(p)['blocked'],'new certified enter clears old restore block')
def fractional(p,ck):
 ck(enter(p,B),'fractional baseline map ready')
 point=p.evaluate('''()=>{const f=MossForest.feet;for(let dx=-96;dx<=96;dx+=16)for(let dy=-96;dy<=96;dy+=16){const x=f.x+dx+0.123456789,y=f.y+dy+0.234567891;if(x>17&&y>42&&x<MossForest.map.world.width&&y<MossForest.map.world.height&&!MossForest.blocked(x,y))return {x,y}}return null}''')
 ck(bool(point),'fractional position is free ground')
 p.evaluate('''point=>{window.point=point;window.pending=MossForest.enter({map:point.map,x:point.x-17,y:point.y-42,transition:"slow"}).then(x=>!!x)}''',dict(point,map=B))
 p.wait_for_function('MossForest.mapRequest.phase==="fading-in"');p.evaluate('MossForest.cancelMapRequest()');ck(p.evaluate('pending') is False,'fractional cancel continuation stopped');ck(not state(p)['unsafe'] and state(p)['save'],'CSS normalization does not falsely stop valid fractional coordinates');ck(p.evaluate('Math.abs(MossForest.feet.x-point.x)<1e-7&&Math.abs(MossForest.feet.y-point.y)<1e-7'),'fractional destination retained precisely')
s.run([(x,lambda p,c,x=x:cancel(p,c,x)) for x in ['MossForest.cancelMapRequest()','MossForest.lock(true)','MossForest.hide()']]+[('mismatch',mismatch),('map identity mismatch',lambda p,c:mismatch(p,c,'id')),('precommit',prepare_cancel),('hook failure',notify_error),('reentry',reentry),('cancel after failed LOAD',after_failed_load),('fractional coordinates',fractional)],8896)
