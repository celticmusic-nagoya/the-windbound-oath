"""LOAD completion must certify the destination, not just return true."""
from map_recovery_support import *
s=Suite('load-commit-recovery')
def legacy(p,ck):
 p.evaluate('px=270.123456789;py=610.234567891;ipx=485.123456789;ipy=575.234567891;camera();inCamera()')
 save(p);saved=stored(p);fail_map(p);assert_stopped(p,ck,'failed commit')
 p.evaluate('renderSystemTab("save")');ck(p.evaluate('loadGrowthData()') is True,'legacy LOAD success');ck(not state(p)['unsafe'] and state(p)['save'],'certified legacy LOAD releases latch')
 ck(p.evaluate('!forestActive&&document.querySelector("#inside").style.display==="block"'),'legacy destination retained, not modernized')
 ck(p.evaluate('MossForest.map===null&&MossForest.snapshot().map===null'),'failed forest retired, invalid mapId not serialized')
 save(p);ck(p.evaluate('document.querySelector("#saveMsg").textContent.includes("セーブしました")'),'SAVE after legacy LOAD succeeds')
 p.evaluate('document.querySelector("#systemMenu").style.display="none"');before=p.evaluate('ipx');p.keyboard.down('ArrowRight');p.wait_for_timeout(160);p.keyboard.up('ArrowRight');ck(p.evaluate('ipx')>before,'restored indoor movement works')
def modern(p,ck):
 ck(enter(p,B),'valid forest initialized');p.evaluate('storyStage=9;forestActive=true');save(p);fail_map(p)
 ck(p.evaluate('loadGrowthData()') is True,'modern LOAD accepted');p.wait_for_function('MossForest.canSave&&MossForest.active',timeout=20000)
 ck(state(p)['map']==B and not state(p)['unsafe'],'modern LOAD final map ready');save(p);ck(p.evaluate('JSON.parse(localStorage.getItem(SAVE_KEY)).prologue.moss.map')==B,'modern SAVE uses restored map')
def invalid(p,ck):
 save(p);fail_map(p);p.evaluate('window.bad=JSON.parse(localStorage.getItem(SAVE_KEY));bad.prologue.version=99;localStorage.setItem(SAVE_KEY,JSON.stringify(bad))')
 ck(p.evaluate('loadGrowthData()') is False,'invalid progress LOAD rejected');p.evaluate('MossForest.lock(false);MossForest.hide();MossForest.resume()');assert_stopped(p,ck,'invalid LOAD')
 old=p.evaluate('({x:px,y:py,ix:ipx})');p.evaluate('forestActive=false;document.querySelector("#inside").style.display="block";document.querySelector("#systemMenu").style.display="none"');p.keyboard.press('ArrowRight');p.wait_for_timeout(100);ck(p.evaluate('({x:px,y:py,ix:ipx})')==old,'incomplete LOAD cannot move legacy or indoor actor')
def incomplete(p,ck):
 save(p);fail_map(p);p.evaluate('window.oldDress=dressRoom;dressRoom=()=>{throw Error("incomplete-room")};renderSystemTab("save")')
 ck(p.evaluate('loadGrowthData()') is False,'partial legacy LOAD reports failure');assert_stopped(p,ck,'partial room LOAD');p.evaluate('dressRoom=oldDress')
 ck(p.evaluate('loadGrowthData()') is True,'retry valid legacy LOAD succeeds');ck(state(p)['save'],'retry certifies state')
def load503(p,ck):
 save(p);p.evaluate('window.d=JSON.parse(localStorage.getItem(SAVE_KEY));d.prologue.storyStage=9;d.prologue.moss={map:"'+B+'",x:300,y:300,opened:[],fired:[]};localStorage.setItem(SAVE_KEY,JSON.stringify(d))');fail_map(p)
 p.route('**/data/maps/'+B+'.json',lambda r:r.fulfill(status=503,body='restore failure'));ck(p.evaluate('loadGrowthData()') is True,'async LOAD initiation accepted');p.wait_for_function('MossForest.mapRequest.phase==="cancelled"',timeout=15000);assert_stopped(p,ck,'async HTTP503');p.unroute_all();ck(enter(p,B),'normal new enter recovers failed LOAD');ck(not state(p)['blocked'] and state(p)['save'],'normal enter clears restore block')
def stale(p,ck):
 save(p);p.evaluate('window.legacy=localStorage.getItem(SAVE_KEY);window.d=JSON.parse(legacy);d.prologue.storyStage=9;d.prologue.moss={map:"'+B+'",x:300,y:300,opened:[],fired:[]};localStorage.setItem(SAVE_KEY,JSON.stringify(d));window.base=ForestLoader;window.waits=[];window.ForestLoader={...base,prepare:async(...a)=>{await new Promise(r=>waits.push(r));return base.prepare(...a)}}');ck(p.evaluate('loadGrowthData()') is True,'first async LOAD accepted');p.wait_for_function('waits.length===1')
 p.evaluate('localStorage.setItem(SAVE_KEY,legacy)');ck(p.evaluate('loadGrowthData()') is True,'new legacy LOAD owns restore');before=state(p);p.evaluate('waits[0]()');p.wait_for_timeout(100);ck(state(p)==before,'stale LOAD completion cannot change successor')
def verification(p,ck):
 save(p);fail_map(p);p.evaluate('window.originalInventory=Inventory;window.Inventory=new Proxy({},{get(o,k){if(k==="reconcile")return ()=>{document.querySelector("#inPlayer").style.left="999px"};return originalInventory[k]}})')
 ck(p.evaluate('loadGrowthData()') is False,'render-position mismatch LOAD denied');assert_stopped(p,ck,'uncertified position');p.evaluate('window.Inventory=originalInventory')
def post_error(p,ck):
 save(p);fail_map(p);p.evaluate('window.originalInventory=Inventory;window.Inventory=new Proxy({},{get(o,k){if(k==="reconcile")return ()=>{throw Error("post-restore-failure")};return originalInventory[k]}})')
 ck(p.evaluate('loadGrowthData()') is False,'post-restore exception reports failure');assert_stopped(p,ck,'outer LOAD incomplete');p.evaluate('window.Inventory=originalInventory')
 ck(p.evaluate('loadGrowthData()') is True,'LOAD after exception succeeds');ck(state(p)['save'],'exception retry revalidated')
def duplicates(p,ck):
 save(p);fail_map(p);p.evaluate('window.originalMoss=MossForest;window.receipt=null;window.MossForest=new Proxy({},{get(o,k){if(k==="finishRestore")return (t,v,k)=>{window.receipt={t,v,k};return originalMoss.finishRestore(t,v,k)};return originalMoss[k]}})')
 ck(p.evaluate('loadGrowthData()') is True,'receipt LOAD succeeds');before=state(p)
 ck(p.evaluate('originalMoss.finishRestore(receipt.t,receipt.v,receipt.k)') is False,'duplicate finish rejected');ck(state(p)==before,'duplicate finish leaves state unchanged')
 p.evaluate('window.MossForest=originalMoss;window.newer=MossForest.beginRestore()');old=state(p)
 ck(p.evaluate('MossForest.failRestore(receipt.t)') is False,'old LOAD failure cannot own new restore');ck(state(p)==old,'old receipt preserves current restore');ck(p.evaluate('MossForest.failRestore(newer)') is True,'current failure owns stop');st=state(p);ck(p.evaluate('MossForest.failRestore(newer)') is False and state(p)==st,'repeated failure cannot reapply cleanup')
def no_receipt(p,ck):
 save(p);fail_map(p);p.evaluate('window.d=JSON.parse(localStorage.getItem(SAVE_KEY));d.prologue.storyStage=9;localStorage.setItem(SAVE_KEY,JSON.stringify(d));window.baseStory=MossForestStory;window.MossForestStory=new Proxy({},{get(o,k){if(k==="fromSave")return ()=>Promise.resolve({id:"'+B+'"});return baseStory[k]}})')
 ck(p.evaluate('loadGrowthData()') is True,'incomplete async LOAD initiated');p.wait_for_timeout(100);assert_stopped(p,ck,'missing mounted-map receipt')
s.run([('legacy',legacy),('modern',modern),('invalid',invalid),('partial',incomplete),('503',load503),('stale',stale),('verification',verification),('post exception',post_error),('duplicate receipt',duplicates),('no receipt',no_receipt)],8895)
