"use strict";
const repo="celticmusic-nagoya/the-windbound-oath", api="https://api.github.com/repos/"+repo;
const targets=[[427,"モルウェン"],[421,"風待ちの崖"],[364,"リルド村"]];
const byId=id=>document.getElementById(id);
function node(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
function tile(parent,title,lines,links=[]){const e=node("article","");e.className="tile";e.append(node("h3",title));for(const line of lines)e.append(node("p",line));for(const [label,path] of links){const a=node("a",label);a.href="https://github.com/"+repo+path;a.rel="noopener noreferrer";e.append(a);}parent.append(e);return e;}
async function read(path){const r=await fetch(api+path,{headers:{"Accept":"application/vnd.github+json"},credentials:"omit",cache:"no-store",signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error("HTTP "+r.status);return r.json();}
async function refresh(automatic=false){const button=byId("refresh");if(button.disabled||automatic&&document.hidden)return;button.disabled=true;const previous=byId("status").textContent;byId("status").textContent="取得中";try{let results;if(automatic){const [pulls,actions]=await Promise.all([read("/pulls?state=all&sort=updated&direction=desc&per_page=100"),read("/actions/runs?per_page=20")]);if(!Array.isArray(pulls)||!Array.isArray(actions?.workflow_runs))throw Error("公開一覧形式不正");const records=targets.map(([n])=>pulls.find(p=>p.number===n&&/^[a-f0-9]{40}$/.test(p.head?.sha||"")&&["open","closed"].includes(p.state)));if(records.some(p=>!p))throw Error("担当PRが最新100件の範囲外。手動取得してください");results=[...records.map(p=>({status:"fulfilled",value:{...p,merged:!!p.merged_at||p.merged===true}})),{status:"fulfilled",value:actions}];window.dispatchEvent(new CustomEvent("studio-live-pulls",{detail:pulls}));}else results=await Promise.allSettled([...targets.map(([n])=>read("/pulls/"+n)),read("/actions/runs?per_page=20")]);if(automatic&&results.some(r=>r.status!=="fulfilled"))throw Error("一部取得失敗");for(const id of ["summary","projects","runs"])byId(id).replaceChildren();const projectJobs=[];let open=0,known=0;targets.forEach(([n,name],i)=>{const r=results[i];if(r.status==="fulfilled"){known++;const p=r.value;if(p.state==="open")open++;const card=tile(byId("projects"),name,["PR #"+n+" / "+(p.merged?"merged":p.state)+(p.draft?" / Draft":""),"HEAD: "+p.head.sha.slice(0,12),"更新: "+p.updated_at,"G1〜G4: 未取得（CI成功≠美術QA）"],[["担当PR","/pull/"+n]]);projectJobs.push(loadProjectRuns(p,card));}else tile(byId("projects"),name,["取得失敗 / "+r.reason.message],[["担当PR","/pull/"+n]]);});tile(byId("summary"),"担当PR",["取得 "+known+" / "+targets.length,"Open "+open+"（取得分のみ）"]);const ar=results[targets.length];if(ar.status==="fulfilled"){const runs=ar.value.workflow_runs;tile(byId("summary"),"Actions（最新20件）",["実行中 "+runs.filter(x=>x.status==="in_progress").length,"待機 "+runs.filter(x=>x.status==="queued"||x.status==="waiting").length]);for(const r of runs){const card=tile(byId("runs"),r.name,[r.status+" / "+(r.conclusion||"未確定"),r.head_branch+" / "+r.head_sha.slice(0,12),r.updated_at],[["実行詳細・Artifacts","/actions/runs/"+r.id]]);const button=node("button","成果物一覧を取得");button.type="button";button.addEventListener("click",()=>loadArtifacts(r,card,button));card.append(button);}}else tile(byId("runs"),"取得失敗",[ar.reason.message],[["Actions一覧","/actions"]]);byId("status").textContent=(results.every(r=>r.status==="fulfilled")?"取得完了":"一部取得失敗")+" / "+new Date().toLocaleString("ja-JP");await Promise.allSettled(projectJobs);return results.every(r=>r.status==="fulfilled");}catch(e){byId("status").textContent="更新失敗: "+e.message+" / 前回表示を保持（"+previous+"）";return false;}finally{button.disabled=false;}}
// Show current revision and older successful runs separately. No additional API request per artifact.
async function loadProjectRuns(p,card){
 const status=node("p","制作中のActions・成果物: 取得中");status.setAttribute("role","status");card.append(status);
 const branch=p.head?.ref,head=p.head?.sha;
 if(typeof branch!=="string"||!/^[a-zA-Z0-9._/-]+$/.test(branch)||!(/^[a-f0-9]{40}$/.test(head||""))){status.textContent="担当ブランチ・HEAD未取得";return;}
 try{
  const data=await read("/actions/runs?branch="+encodeURIComponent(branch)+"&per_page=20");
  if(!card.isConnected)return;
  if(!Array.isArray(data.workflow_runs))throw Error("Actions形式不正");
  const runs=data.workflow_runs.filter(x=>x&&x.head_branch===branch&&/^[a-f0-9]{40}$/.test(x.head_sha||"")&&Number.isSafeInteger(x.id)&&x.id>0&&typeof x.name==="string"&&typeof x.status==="string");
  const date=x=>Number.isFinite(Date.parse(x.updated_at))?Date.parse(x.updated_at):0;
  runs.sort((a,b)=>date(b)-date(a)||b.id-a.id);
  const current=runs.filter(x=>x.head_sha===head),prior=runs.find(x=>x.head_sha!==head&&x.status==="completed"&&x.conclusion==="success");
  status.textContent="ブランチ最新20件内 / 現HEAD "+current.length+" run / 過去HEADとは区別（CI成功≠美術QA）";
  const add=(run,parent,kind)=>{
   const item=node("div","");item.className="project-run";item.dataset.runId=String(run.id);item.dataset.revision=kind;
   item.append(node("p",run.name+" / "+run.status+" / "+(run.conclusion||"未確定")),node("p","HEAD: "+run.head_sha.slice(0,12)+" / "+(run.updated_at||"日時不明")));
   const link=node("a","実行詳細・Artifacts");link.href="https://github.com/"+repo+"/actions/runs/"+run.id;link.rel="noopener noreferrer";item.append(link);
   const button=node("button","このrunの成果物一覧");button.type="button";button.addEventListener("click",()=>loadArtifacts(run,item,button));item.append(button);parent.append(item);
  };
  const group=node("details","");group.className="project-current-runs";group.open=true;group.append(node("summary","現HEADのActions（"+current.length+"件）"));card.append(group);
  if(!current.length)group.append(node("p","現HEADのrun未検出（取得範囲内）"));
  for(const run of current.slice(0,5))add(run,group,"current");
  if(current.length>5)group.append(node("p","表示上限5件。全件は担当PRまたはActionsを参照。"));
  if(prior){const history=node("details","");history.className="project-prior-run";history.append(node("summary","過去HEADの直近成功run（現HEADの証跡ではない）"));add(prior,history,"prior");card.append(history);}
  const all=node("a","担当ブランチのActions一覧");all.href="https://github.com/"+repo+"/actions?query=branch%3A"+encodeURIComponent(branch);all.rel="noopener noreferrer";card.append(all);
 }catch(e){if(card.isConnected)status.textContent="現HEADのActions取得失敗: "+e.message;}
}
// One bounded dashboard cycle (bulk PR list + global runs + three exact branch lists).
// The recent artifact panel owns its separate 5-minute cycle; avoid 60/hour anonymous API exhaustion.
let overviewTimer=null,overviewDue=0,overviewBusy=false;
const overviewNote=node("p","担当PR・Actionsは表示中15分ごとに自動取得（手動取得可）。非表示時は停止。");overviewNote.className="note";byId("status").after(overviewNote);
function scheduleOverview(){if(overviewTimer!==null)clearTimeout(overviewTimer);overviewTimer=null;if(!document.hidden&&!overviewBusy)overviewTimer=setTimeout(()=>refreshOverview(true),Math.max(0,overviewDue-Date.now()));}
async function refreshOverview(automatic=false){
 if(overviewBusy||automatic&&document.hidden)return;
 overviewBusy=true;if(overviewTimer!==null)clearTimeout(overviewTimer);overviewTimer=null;
 try{const ok=await refresh(automatic);overviewDue=Date.now()+(ok?900000:1800000);}
 finally{overviewBusy=false;scheduleOverview();}
}
byId("refresh").addEventListener("click",()=>refreshOverview(false));
document.addEventListener("visibilitychange",scheduleOverview);
refreshOverview();

// Discover active area-design work without guessing a PR number.
// The listing is read-only and labels candidates rather than claiming adoption.
// Evidence-based coarse maturity, not a measured fraction of work/time or formal G1-G4.
const AREA_SNAPSHOT={"date":"2026-11-26","heads":{"357":"1c8d0ebf69022f83806a837669ce57156b0dbb68","364":"8e800246b16125506c46a051588b7ad18905ace6","421":"58cf4ea27ca800dc4cd236149b5035c4f324ba54","482":"3440af1b22a9c87c55237bab25921aa20aa80d34"},"stages":[["構想・範囲",10],["詳細設計",20],["3D形状",25],["材質・美術",20],["ゲーム統合",15],["独立QA・採用",10]],"areas":[["RILDE_VILLAGE","リルド村",[1,0.5,0.5,0.5,0,0],"港V13・エイダン家の局所native再読込／進入検証。村全体の地形・接続未確定。",[["港・境界設計 V13","RILDE_HARBOR_BOUNDARY_RECEIPT_V13.json"],["エイダン家・実原本検査",364,"7161592250"]],[482,364]],["WINDWAITING_CLIFF","風待ちの崖",[1,0.5,0.5,0.5,0,0],"局所岩盤と材質候補・C11比較画像あり。全域地形・美術・ゲームQA未完了。",[["全域空間設計候補","WINDWAITING_CLIFF_AREA_SPATIAL_CANDIDATE_V01.json"],["C11制作・来歴QA",421,"7163650681"]],[482,421]],["COASTAL_MEADOW","海岸草原",[1,0.5,0.5,0.5,0,0],"暫定領域設計と草地・植生の局所3D候補。草地G2 FAIL、全域配置未実施。",[["8エリア暫定平面図","RILDE_AREA_FIRST_PLAN_V03.svg"],["植生統合候補・独立レビュー",357,"7038851582"],["海岸草地・G2 FAIL",357,"7030143387"]],[482,357]],["RIVER_CORRIDOR","河川回廊",[1,0.5,0.5,0.5,0,0],"河川網V26・水深材質V34・局所接続V44。支流・全域配置・ゲーム未検証。",[["河川網設計 V26","RILDE_C03_RIVER_NETWORK_DESIGN_V26.json"],["河川中心部メッシュ V27","RILDE_C03_RIVER_CORE_MESH_RECEIPT_V27.json"],["下流メッシュ V28","RILDE_C03_LOWER_RIVER_MESH_RECEIPT_V28.json"],["水深・材質 V34","RILDE_C03_DEPTH_WATER_RECEIPT_V34.json"],["河川・森林局所接続 V44","RILDE_C03_FOREST_TERRAIN_INTEGRATION_RECEIPT_V44.json"]],[482]],["MOSS_FOREST_A1","モスの森 A1",[1,0.5,0.5,0,0,0],"V45D局所経路GLB・勾配検査、河岸V12 HOLD。全域native・植生・ゲーム未確認。",[["林縁経路設計","MOSS_FOREST_TRAIL_DESIGN_V02.json"],["河岸・地形設計 V12","MOSS_FOREST_BANK_LANDFORM_RECEIPT_V12.json"],["地形追従経路 V45D","MOSS_FOREST_CONFORMING_TRAIL_RECEIPT_V45D.json"]],[482]],["MOSS_FOREST_A2","モスの森 A2",[1,0.5,0.5,0.5,0,0],"谷・接合部V12と局所PBR/配置V51の記録。全域地形・水系・美術HOLD。",[["谷・接合部 V12","MOSS_FOREST_A2_JUNCTION_TOPOLOGY_RECEIPT_V12.json"],["写真PBR・配置 V51","MOSS_FOREST_A2_PHOTO_PBR_RECEIPT_V51.json"]],[482]],["MOSS_FOREST_A3","モスの森 A3",[1,0.5,0.5,0.5,0,0],"聖域V57/V58、主要樹木V56、小遺跡V66。独立D4・全域配置・G2/G4未完了。",[["聖域・景観 V58","MOSS_FOREST_SANCTUARY_SCENIC_RECEIPT_V58.json"],["小遺跡設計 V64","MOSS_FOREST_SMALL_RUINS_BLUEPRINT_RECEIPT_V64.json"],["遺跡・局所操作検証 V66","MOSS_FOREST_SMALL_RUINS_OPERATION_AUDIT_RECEIPT_V66.json"]],[482]],["DUNVAR_FORTRESS","ドゥンヴァル砦",[1,0,0,0,0,0],"暫定配置・設計要求のみ確認。砦固有の精密設計・native・ゲーム証跡未確認。",[["8エリア平面・断面設計枠","RILDE_EIGHT_AREA_PLAN_SECTION_SLOTS_V01.svg"],["8エリア接続監査","RILDE_EIGHT_AREA_INTERFACE_RECONCILIATION_V01.json"]],[482]]]};
const AREA_MODULES={"RILDE_VILLAGE":[{"name":"集落地形・境界","levels":[1,0.5,0,0,0,0],"note":"暫定配置・実測未確定","source":"RILDE_AREA_FIRST_PLAN_V03.json","blob":"f5c7313464c9e6020c72cbd291caff5dd19e1fbb","owner":482,"comment":null},{"name":"漁港・岸壁","levels":[1,0.5,0,0,0,0],"note":"境界サンプル設計、原地形・D4 HOLD","source":"RILDE_HARBOR_BOUNDARY_RECEIPT_V13.json","blob":"86014e2e1d737f0f2a5ffa6ad626560f969620c8","owner":482,"comment":null},{"name":"住宅・内装","levels":[1,0.5,0.5,0.5,0,0],"note":"HOME候補と実原本外部進入検証／全住宅未確認","source":null,"blob":null,"owner":364,"comment":"7161592250"},{"name":"橋・道路","levels":[1,0.5,0,0,0,0],"note":"橋輪石設計、支持面HOLD","source":"RILDE_BRIDGE_RING_BLUEPRINT_RECEIPT_V05.json","blob":"8ed9d363e0e6a602f187c63fc44c0b616e20dad2","owner":482,"comment":null}],"WINDWAITING_CLIFF":[{"name":"岩盤・崖面","levels":[1,0.5,0.5,0.5,0,0],"note":"C11局所造形・CC0材質候補、全域未採用","source":null,"blob":null,"owner":421,"comment":"7163650681"},{"name":"台地・通行経路","levels":[1,0.5,0.5,0,0,0],"note":"局所空間メッシュ・経路中心線候補、衝突未検証","source":"WINDWAITING_CLIFF_AREA_SPATIAL_CANDIDATE_V01.json","blob":"81e14da2ebb23adc4bb6ac63691d8d5d6b85f617","owner":482,"comment":null},{"name":"地層・崩落周辺植生","levels":[0,0,0,0,0,0],"note":"全域の植生配置・崩落との接続未確認","source":null,"blob":null,"owner":421,"comment":null}],"COASTAL_MEADOW":[{"name":"草原地形・農地","levels":[1,0.5,0,0,0,0],"note":"暫定エリア平面のみ、標高・排水未確定","source":"RILDE_AREA_FIRST_PLAN_V03.json","blob":"f5c7313464c9e6020c72cbd291caff5dd19e1fbb","owner":482,"comment":null},{"name":"草花・低木・芝","levels":[1,0.5,0.5,0.5,0,0],"note":"ECO統合候補／草地の美術課題残存","source":null,"blob":null,"owner":357,"comment":"7038851582"},{"name":"生垣・作物・水路","levels":[0,0,0,0,0,0],"note":"当該エリアへの配置未確認","source":null,"blob":null,"owner":357,"comment":null}],"RIVER_CORRIDOR":[{"name":"河川網・縦横断面","levels":[1,0.5,0,0,0,0],"note":"V26暫定水系・物理流量未確定","source":"RILDE_C03_RIVER_NETWORK_DESIGN_V26.json","blob":"dc2051c9e9b876d262c08f557e8816ece8e12ba2","owner":482,"comment":null},{"name":"河床・河岸・接続","levels":[1,0.5,0.5,0,0,0],"note":"V44局所GLB接続・EGL診断、全域未確定","source":"RILDE_C03_FOREST_TERRAIN_INTEGRATION_RECEIPT_V44.json","blob":"786d45035c04f397400876bb13f923c1513d7225","owner":482,"comment":null},{"name":"水面・水深・材質","levels":[1,0.5,0.5,0.5,0,0],"note":"V34深度α局所GLB・CPU比較、物理流水・ゲーム未検証","source":"RILDE_C03_DEPTH_WATER_RECEIPT_V34.json","blob":"59cc241e25365a220cb5788c166e63d5fdb9c217","owner":482,"comment":null},{"name":"橋・護岸","levels":[1,0.5,0,0,0,0],"note":"輪石設計、支持面HOLD","source":"RILDE_BRIDGE_RING_BLUEPRINT_RECEIPT_V05.json","blob":"8ed9d363e0e6a602f187c63fc44c0b616e20dad2","owner":482,"comment":null},{"name":"支流・海への接続","levels":[1,0.5,0,0,0,0],"note":"V28下流候補、支流掘削・海面未完成","source":"RILDE_C03_LOWER_RIVER_MESH_RECEIPT_V28.json","blob":"f1d8ce3e7fcf75514c3d44c9387ff84d1f909477","owner":482,"comment":null}],"MOSS_FOREST_A1":[{"name":"林縁・進入路","levels":[1,0.5,0.5,0,0,0],"note":"V45D局所経路GLB、勾配数値検査、native／衝突未確認","source":"MOSS_FOREST_CONFORMING_TRAIL_RECEIPT_V45D.json","blob":"289817f02e4b2fb2b21d4530123465b5264c79d8","owner":482,"comment":null},{"name":"河岸・上陸地点","levels":[1,0.5,0,0,0,0],"note":"過大切土・岸接続HOLD","source":"MOSS_FOREST_BANK_LANDFORM_RECEIPT_V12.json","blob":"bb8545431171fb51103522b00223d879d1605d2e","owner":482,"comment":null},{"name":"植生・樹木配置","levels":[0,0,0,0,0,0],"note":"A1固有の配置未確認","source":null,"blob":null,"owner":482,"comment":null}],"MOSS_FOREST_A2":[{"name":"谷・地形接合","levels":[1,0.5,0,0,0,0],"note":"V12局所接合設計、全域地形未確定","source":"MOSS_FOREST_A2_JUNCTION_TOPOLOGY_RECEIPT_V12.json","blob":"6fdfb7f1856a5c4a83787f72d3492373821123dc","owner":482,"comment":null},{"name":"小川・南側排水","levels":[1,0.5,0.5,0,0,0],"note":"V48B局所排水メッシュ、出口D4 HOLD","source":"MOSS_FOREST_A2_SOUTH_DRAINAGE_RECEIPT_V48B.json","blob":"36182b9ceb509d8500b68afbff602dd134212a66","owner":482,"comment":null},{"name":"植生・林冠配置","levels":[1,0.5,0,0,0,0],"note":"V09配置計画、実アセット未統合","source":"MOSS_FOREST_A2_ECOLOGY_RELAYOUT_DESIGN_V09.json","blob":"2110c507b3011ecbbda630201b0ccf30dbd8a841","owner":482,"comment":null},{"name":"岩・林床材質","levels":[1,0.5,0.5,0.5,0,0],"note":"V51局所GLBと写真PBR、自己美術HOLD","source":"MOSS_FOREST_A2_PHOTO_PBR_RECEIPT_V51.json","blob":"4141aa6349807c015fd19951eca0610c1bda682b","owner":482,"comment":null}],"MOSS_FOREST_A3":[{"name":"聖域・景観","levels":[1,0.5,0.5,0.5,0,0],"note":"V57実native／V58景観候補、全域・美術HOLD","source":"MOSS_FOREST_SANCTUARY_SCENIC_RECEIPT_V58.json","blob":"bfdc1d8d55700c5f6fc2e74230a34c7752c3d439","owner":482,"comment":null},{"name":"主要樹木","levels":[1,0.5,0.5,0.5,0,0],"note":"V56スキャン適応、樹冠不一致HOLD","source":"MOSS_FOREST_HERO_TREE_SCAN_ADAPTATION_RECEIPT_V56.json","blob":"0ae3de21886fdacfb86a97edbbf09fae62ccc5a7","owner":482,"comment":null},{"name":"遺跡・石碑","levels":[1,0.5,0.5,0,0,0],"note":"V66局所溝試験のみ、独立D4・native未実施","source":"MOSS_FOREST_SMALL_RUINS_OPERATION_AUDIT_RECEIPT_V66.json","blob":"4cf2f9a42fe885f6a772fb206208661c34f24d58","owner":482,"comment":null},{"name":"祭壇進入路・地形","levels":[1,0.5,0.5,0,0,0],"note":"V47B局所接続面、外周・排水HOLD","source":"MOSS_FOREST_SANCTUARY_APPROACH_RECEIPT_V47B.json","blob":"6bff1d308103ed77b07c9abe244956957dce8f6f","owner":482,"comment":null}],"DUNVAR_FORTRESS":[{"name":"砦の位置・エリア範囲","levels":[1,0,0,0,0,0],"note":"暫定配置のみ","source":"RILDE_AREA_FIRST_PLAN_V03.json","blob":"f5c7313464c9e6020c72cbd291caff5dd19e1fbb","owner":482,"comment":null},{"name":"城壁・門・建築","levels":[0,0,0,0,0,0],"note":"砦固有3D制作証跡未確認","source":null,"blob":null,"owner":482,"comment":null},{"name":"高地地形・進入路・排水","levels":[0,0,0,0,0,0],"note":"砦固有設計未確認","source":null,"blob":null,"owner":482,"comment":null}]};
const AREA_BASELINE_FILES={"ALVERIA_C03_HYDROLOGY_SKELETON_V26.json":"1254699957fbb0d2e8e399680c6bb911d44d8cd0","ALVERIA_HIERARCHICAL_ATLAS_V01.json":"a40c72b68678f00fdcf1e1a5992c894a509e4f35","ALVERIA_KINGDOM_MAP_CANDIDATE_V01.json":"d05478e6da41ace5022b622f985d63fcbacb740c","ALVERIA_RELATIVE_TERRAIN_V01.json":"591c81ee131fe800c314f65f0f691ce888528649","ALVERIA_W01_CONTINENT_TO_REGION_TOPOLOGY_V01.json":"484fee575101559fa084f9b6226fe6cf0d2ce20b","ALVERIA_W02_C01_COASTLINE_CANDIDATE_V01.json":"72e1e488bbe4c92fc5d473139d8eb1d00d07b084","ALVERIA_W02_C01_LOCATOR_AND_SOURCE_QA_V01.json":"6087c8b8ca763e9180117dba91ad7b6c4961d271","MOSS_FOREST_A2_ECOLOGY_DESIGN_V04.json":"1d531573f7629928d6928a69fe22b9569264e684","MOSS_FOREST_A2_ECOLOGY_RECEIPT_V04.json":"51cc7574dac4a0141dafb9edec36dd3b8de0358a","MOSS_FOREST_A2_ECOLOGY_RELAYOUT_DESIGN_V09.json":"2110c507b3011ecbbda630201b0ccf30dbd8a841","MOSS_FOREST_A2_ECOLOGY_RELAYOUT_RECEIPT_V09.json":"87e18f459f6d42dc5892517597ae0edd723eb81f","MOSS_FOREST_A2_HYDROLOGY_RECEIPT_V03.json":"11c39295f270d328b1a7c7acd01bea60434698bd","MOSS_FOREST_A2_JUNCTION_LOD_RECEIPT_V10.json":"e9254a08301a3c06ba4e41490710097b0bdfcb33","MOSS_FOREST_A2_JUNCTION_PRECISION_QA_V12.json":"c3fecc78ac20b5edc8c69369e1694ab553b7ffe2","MOSS_FOREST_A2_JUNCTION_TOPOLOGY_RECEIPT_V12.json":"6fdfb7f1856a5c4a83787f72d3492373821123dc","MOSS_FOREST_A2_MATERIAL_STUDY_RECEIPT_V50.json":"dd602538dcb035d4ea8ff6dab0ee8f2b8710e179","MOSS_FOREST_A2_OUTLET_DESIGN_RECEIPT_V49.json":"4bcb64dc10f64c97f87c1f4f073b92b79837f806","MOSS_FOREST_A2_OVERLOOK_DESIGN_V06.json":"d5a644afeb7fbb8e5f54abd3b5e7d99bdbf2378f","MOSS_FOREST_A2_OVERLOOK_RECEIPT_V06.json":"81fe45e9b1fac988f3eec7eeb7b48530541a2688","MOSS_FOREST_A2_OVERLOOK_REFINEMENT_RECEIPT_V07.json":"e1a7c480b4afdc249bfe6a1d12e077d1cc31e576","MOSS_FOREST_A2_PHOTO_PBR_RECEIPT_V51.json":"4141aa6349807c015fd19951eca0610c1bda682b","MOSS_FOREST_A2_SOUTH_DRAINAGE_RECEIPT_V48B.json":"36182b9ceb509d8500b68afbff602dd134212a66","MOSS_FOREST_A2_VALLEY_RECEIPT_V02.json":"845a48ab8b63f83e16135baa3e1534ef1fddf0bc","MOSS_FOREST_A2_VIEW_LOD_DESIGN_V05.json":"ab06ecb10d17dfc96638aa2a9451a8e62de6c70b","MOSS_FOREST_A2_VIEW_LOD_RECEIPT_V05.json":"5e19c7571892f60a4f2be678ccd73298dcd49949","MOSS_FOREST_A3_GATE_LOCAL_CONTRACT_V04.json":"e45210ba8925df3eec04d3ad12ae4bd29512d158","MOSS_FOREST_A3_GATE_LOCAL_QA_V04.json":"733eb5f677a3ca71c1b5865b2c2315cdb10f720c","MOSS_FOREST_A3_GATE_LOCAL_RECEIPT_V04.json":"a49e5ba1aff2b7ab27ed970e59e3e51b775de4fe","MOSS_FOREST_A3_GATE_RECEIPT_V03.json":"a52575bbab67ad1673c40c8b6d90a68b87c50bf5","MOSS_FOREST_A3_LANDMARKS_DESIGN_V05.json":"246095359e151284e447a30c203d33f36cedbe77","MOSS_FOREST_A3_LANDMARKS_RECEIPT_V05.json":"f379123111a6a26b3c43af34f9232ed622c81e58","MOSS_FOREST_A3_MATERIAL_STUDY_RECEIPT_V07.json":"922e21c8cecfae1ca545502996405849d5158fab","MOSS_FOREST_A3_SANCTUARY_DESIGN_V01.json":"d640ef49f81531cc2b714b7d25150747c982f450","MOSS_FOREST_A3_SANCTUARY_RECEIPT_V01.json":"70f5cdc199e6e1e7d7bc644c6badf6380703c8d5","MOSS_FOREST_A3_STAGING_RECEIPT_V02.json":"f51f4a25925ba279fa44fa6053fa75f9f813d8bf","MOSS_FOREST_A3_SURFACE_DESIGN_V06.json":"acbbffca333b087ee3dc93fd89da4c6940ff2792","MOSS_FOREST_A3_SURFACE_RECEIPT_V06.json":"220144dc1d823e8dfde6f77038d94e5149559eb5","MOSS_FOREST_ALTAR_MASONRY_RECEIPT_V62.json":"cfe7c94b15a0c48a06ef65ef7fcad7586849b999","MOSS_FOREST_ALTAR_TERRACE_RECEIPT_V61.json":"ac7d6da856d9640813fade31eb149608ad02d852","MOSS_FOREST_BANK_LANDFORM_DESIGN_V12.json":"740a6dcaff5eaba624b941b8ab3bafb20757b81e","MOSS_FOREST_BANK_LANDFORM_RECEIPT_V12.json":"bb8545431171fb51103522b00223d879d1605d2e","MOSS_FOREST_BANK_ROUTE_DESIGN_V08.json":"7e59c955e49dec73d3b72678574dbe0e0ddc544f","MOSS_FOREST_BANK_SHOULDER_TANGENT_RECEIPT_V08.json":"815d537f6b2f9a105d01608b72a6114dc9968ed3","MOSS_FOREST_BANK_ZONES_DESIGN_V09.json":"2ccd8edb0578183cca860b22a0aac60f069e30d9","MOSS_FOREST_BANK_ZONES_RECEIPT_V09.json":"168af298123b1828d04175325b22f2b7b6e34fd5","MOSS_FOREST_CONFORMING_TRAIL_RECEIPT_V45D.json":"289817f02e4b2fb2b21d4530123465b5264c79d8","MOSS_FOREST_ENDPOINTS_BANK_RECEIPT_V06.json":"afe5f9cc2340affe83d0d925b60435f0f7ce2e8f","MOSS_FOREST_HERO_TREE_RECEIPT_V54.json":"069393cc0d823c81f302c87a538c06e133d49cd8","MOSS_FOREST_HERO_TREE_SCAN_ADAPTATION_RECEIPT_V56.json":"0ae3de21886fdacfb86a97edbbf09fae62ccc5a7","MOSS_FOREST_HERO_TREE_SOURCE_RECEIPT_V55.json":"fea787b27a00f3bdb3d3adc160db2f126fedcf37","MOSS_FOREST_HERO_TREE_SOURCE_RESULT_V55.json":"381a2363c223bcdfa00574f08c5d3cbcb4ad276c","MOSS_FOREST_LANDING_METHOD_STOP_RECEIPT_V11.json":"7f6bb9af6091cbe77f8270268b8c170444a840de","MOSS_FOREST_NATIVE_INTERFACE_RECEIPT_V52.json":"2956b679a43a4ee01604314a526a4f63e41d7d30","MOSS_FOREST_RUINS_BLUEPRINT_DESIGN_V59.json":"3a44610dc4d73fa89367a2fa049ae96dee49948c","MOSS_FOREST_RUINS_BLUEPRINT_RECEIPT_V59.json":"fe095dc687faacdecbb302ecf439462b2924f1bb","MOSS_FOREST_RUINS_DETAILED_BLUEPRINT_RECEIPT_V60.json":"aaa80fa8d33c8cadc525aac052ce8b153fd598f1","MOSS_FOREST_RUINS_SURFACE_RECEIPT_V63.json":"fbfa17f56dc1505e65afccb6d52382182649d9fd","MOSS_FOREST_SANCTUARY_APPROACH_RECEIPT_V47B.json":"6bff1d308103ed77b07c9abe244956957dce8f6f","MOSS_FOREST_SANCTUARY_LANDMARK_RECEIPT_V53.json":"2a9710402f171c4797e4ce97523430d1e59ea9f6","MOSS_FOREST_SANCTUARY_PAD_RECEIPT_V46B.json":"cca4d08957aec2d24b8b0507a2c41a19b7174c9d","MOSS_FOREST_SANCTUARY_SCENE_RECEIPT_V57.json":"a72e3f0f5cf3c42cfbf63c87499c912208c72701","MOSS_FOREST_SANCTUARY_SCENIC_RECEIPT_V58.json":"bfdc1d8d55700c5f6fc2e74230a34c7752c3d439","MOSS_FOREST_SHOULDER_RECEIPT_V03.json":"cd29e56b27b445e6a2e1b179483372145eed8733","MOSS_FOREST_SMALL_RUINS_BLUEPRINT_RECEIPT_V64.json":"6891eaa983a22c8eb70e7723da5e0286b0d014a8","MOSS_FOREST_SMALL_RUINS_MATERIAL_FRACTURE_RECEIPT_V65.json":"7b9cda557ea4eba6b21170a82b35b197a5872c86","MOSS_FOREST_SMALL_RUINS_OPERATION_AUDIT_RECEIPT_V66.json":"4cf2f9a42fe885f6a772fb206208661c34f24d58","MOSS_FOREST_TRAIL_DESIGN_V01.json":"1d3d7e49813c6e4c865823a9bfa941dd6dc74026","MOSS_FOREST_TRAIL_DESIGN_V02.json":"053220f5bb45e95aa31f3d4296f98d95f25d05e9","MOSS_FOREST_TRAIL_RECEIPT_V02.json":"d3c22be28b559cf728060aab8239b62888fb5103","RILDE_ACCESS_BRIDGE_CANDIDATE_V03.json":"250c61114b4779b6349bfbc3c4f6ae2eeacb9b9a","RILDE_AREA_FIRST_PLAN_V03.json":"f5c7313464c9e6020c72cbd291caff5dd19e1fbb","RILDE_BRIDGE_BANK_CALIBRATION_V04.json":"5c03201d2e177ffa4dd7eb52d0d7e995e878b914","RILDE_BRIDGE_RECOVERY_CONTACT_AUDIT_V01.json":"8867c0ac5c3d784e0e7a8123020f9ef101653ff9","RILDE_BRIDGE_RING_BLUEPRINT_RECEIPT_V05.json":"8ed9d363e0e6a602f187c63fc44c0b616e20dad2","RILDE_C01_C03_AREA_INTERFACE_V01.json":"d1b48b33672e11cc97f4a5632247206196385563","RILDE_C01_C03_DIRECTIONAL_V01.json":"909f72f92b7c6d1b3e1c1ccc12455cb19f7c00ee","RILDE_C01_C03_TOPOLOGY_CONSTRAINTS_V01.json":"6271915f1eaf37e1cd46850d422ceb1318fbb8bb","RILDE_C02_C03_SECTION_HYDROLOGY_V01.json":"00c9699b7496954270bcbb76664db594539b230e","RILDE_C03_ASYMMETRIC_BANK_DESIGN_RECEIPT_V42C.json":"42493321072329b8a1002b3481a3968d1e30bd6b","RILDE_C03_BANK_LOD_RECEIPT_V36.json":"aeafc4d5dab65d03e8eeadb683d66d0fa127b1f3","RILDE_C03_BANK_ROCK_RECEIPT_V35.json":"099c96196183d4960327deb8c0b880c49e70f684","RILDE_C03_BANK_SECTION_SURVEY_RECEIPT_V41.json":"7e94f81c9a67639b3ef342c952223aad2a45aa4e","RILDE_C03_DEPTH_WATER_RECEIPT_V34.json":"59cc241e25365a220cb5788c166e63d5fdb9c217","RILDE_C03_EAST_BANK_EXPANSION_RECEIPT_V43B.json":"d7901304520488747e40cc52afec2d6c784c2286","RILDE_C03_EGL_RENDER_VALIDATION_RECEIPT_V40.json":"56f2785fd662ea183df84b3acdf4db76e864110f","RILDE_C03_FERN_GRAVEL_RECEIPT_V37.json":"2ec1687a32e7931cb0bc6c0953a98a4ffa275978","RILDE_C03_FOREST_INTERFACE_RECEIPT_V32.json":"95d0d78eac64573523e26f1a823934bd4bbf6cf2","RILDE_C03_FOREST_TERRAIN_INTEGRATION_RECEIPT_V44.json":"786d45035c04f397400876bb13f923c1513d7225","RILDE_C03_LANDING_ALIGNMENT_RECEIPT_V31.json":"67b9e54f7f0a2bc73c731c36334fc989c8a30f51","RILDE_C03_LOWER_RIVER_MESH_RECEIPT_V28.json":"f1d8ce3e7fcf75514c3d44c9387ff84d1f909477","RILDE_C03_MATERIAL_RECEIPT_V33.json":"67f4864449d1437902d0172f1f799b3c15b14351","RILDE_C03_NATIVE_INTAKE_OPTIMIZATION_RECEIPT_V39.json":"173de657c4d0d627b57d05028679547b30c2fa47","RILDE_C03_RIPARIAN_COMPOSITION_RECEIPT_V38B.json":"f025c52a792c23aedb45384f8403d60b34654404","RILDE_C03_RIVER_CORE_MESH_RECEIPT_V27.json":"8973ebc6e85d92fb27eb347e1dc89df38497c73e","RILDE_C03_RIVER_NETWORK_DESIGN_V26.json":"dc2051c9e9b876d262c08f557e8816ece8e12ba2","RILDE_C03_TRIBUTARY_MESH_RECEIPT_V29.json":"21025320fb12e0929ae85454d16e54f15ecc760d","RILDE_C03_VALLEY_IMPROVEMENT_RECEIPT_V30B.json":"f8eba35b67c6e928ec6b22623bacfc8384737f44","RILDE_CORE_AREA_SURFACES_V01.json":"21b2804db198aaf9429f5f959d68a955e5839593","RILDE_EIGHT_AREA_INTERFACE_RECONCILIATION_V01.json":"bc28c422352546f81f8922ed8f5b913efdd81266","RILDE_EIGHT_AREA_PLAN_SECTION_SLOTS_V01.json":"300fa1fa080886abdb1493039a41fe6449633cb0","RILDE_EXPANSION_SURFACES_V02.json":"dc06678c3ac274b2d2b63de0926b42bde9758504","RILDE_HARBOR_ACCESS_RECEIPT_V07.json":"066a67f364238bf82cf0007f998a11541b1cb836","RILDE_HARBOR_BASIN_RECEIPT_V04.json":"f73af6186f7cef5ab714ec690e8f01dbfb1fd6d0","RILDE_HARBOR_BOUNDARY_RECEIPT_V13.json":"86014e2e1d737f0f2a5ffa6ad626560f969620c8","RILDE_HARBOR_DESIGN_RECEIPT_V02.json":"1bb8cb6e4d92d54f090acc4b68ccf1ff5263d752","RILDE_HARBOR_INTERFACE_RECEIPT_V09.json":"65ae83999cd596d1d26709a83e36cd202db32774","RILDE_HARBOR_QUAY_DESIGN_V08.json":"f554cb46eb30e8fc05361a130e29617808dc37e8","RILDE_HARBOR_QUAY_RECEIPT_V08.json":"44d642692d296a71d70d31c1ec20b32f50c5d0e0","RILDE_HARBOR_ROAD_SLOPE_CALIBRATION_V09.json":"015e0686eae7acc77d63240f406df31afacf6b68","RILDE_HARBOR_TERRAIN_DESIGN_RECEIPT_V11.json":"14ac512a999de62d3ca7f4b040bf55d577ef93ce","RILDE_HARBOR_TRANSITION_DESIGN_V12.json":"1e23801f0e0d2830c52dc5c9efde17952cdec668","RILDE_HARBOR_TRANSITION_RECEIPT_V12.json":"a2025cc84f82515a4c7579966bb191cfad1fdfe7","RILDE_PROVISIONAL_SCHEMATIC_LAYOUT_V01.json":"d71b5ec3de5fd03a14151bdbb041a63e307e2929","RILDE_PROVISIONAL_SCHEMATIC_LAYOUT_V02.json":"9f681d26c7aa9e421c143433b6d2603209b0f57a","RILDE_RECOVERED_ACCESS_BASELINE_V03.json":"5aade3829bcc608e19fe28b644d0ab8aa96dd7cc","RILDE_TERRAIN_RECOVERY_RECEIPT_V01.json":"a9ebd0569ef2626c82be8a17c26477cd77229a30","RILDE_TOP_DOWN_LOCAL_ENVELOPE_QA_V22.json":"1f541f8e0ee6a98c0f283ba62869b22b61b379ef","SHARED_FOREST_BIOME_QA_V04.json":"92ec34742f6885366f3b6e7e6b61383dc74c1fd0","SHARED_FOREST_BIOME_RECEIPT_V04.json":"735689eb37f6664858d6f0a6e5cee3f4a7cd0156","SHARED_FOREST_COLONY_SHADOW_RECEIPT_V14.json":"55ef5954607c07a78516d8283306c911c94dd00c","SHARED_FOREST_ECO_ASSEMBLY_RECEIPT_V10.json":"0b7654d48f61d4789f65426911f7a589b17023cb","SHARED_FOREST_GROUND_DEPTH_RECEIPT_V15.json":"2ed01876b13ee1d20ee4ba0a714b3818c9859717","SHARED_FOREST_MATERIAL_APPLICATION_QA_V03.json":"e3a3914fa6d3f777983c7d3895ed780a3e4122a3","SHARED_FOREST_NATIVE_DENSITY_DRIVE_ADAPTER_RECEIPT_V18.json":"f83603b585d9e8671701a080f7d78db10c22a111","SHARED_FOREST_NATIVE_RECOVERY_FLOOR_KIT_RECEIPT_V20.json":"5fab0cdfe5b6cfb126eda7315c995ef86ecee609","SHARED_FOREST_NATIVE_TRANSITION_RECEIPT_V16.json":"3e2912dce3b7c577c4be880b5d7d6610f7a3ac76","SHARED_FOREST_OFFICIAL_CG_NATIVE_FLOOR_RECEIPT_V21.json":"8b4ff58d4c3a48ad3651cd97471cd9884c01bfc6","SHARED_FOREST_PHOTO_FERN_BARK_LOD_RECEIPT_V13.json":"0ec7206007ae89017d6a7d4408313b92160d0852","SHARED_FOREST_PHOTO_REFERENCE_COMPOSITION_RECEIPT_V11.json":"ef82b7c232204bd2ee0c344cdfbc2b2833c779dd","SHARED_FOREST_PRIVATE_DRIVE_NATIVE_PILOT_RECEIPT_V17.json":"3501adcdffa7f75084002bbc209cff9a7108397e","SHARED_FOREST_ROCK_LOD_RECEIPT_V05.json":"d4dfac77854d85f796aec1db9ee5861e2efa6e3e","SHARED_FOREST_ROCK_MATERIAL_RECEIPT_V08.json":"43d80e1419b169ef4ffcd28523b963c3a34888da","SHARED_FOREST_ROCK_RECOVERY_RECEIPT_V07.json":"cc9d9595d95d8b41223e7d8ae1bca16386f20c94","SHARED_FOREST_TERRAIN_ASSEMBLY_RECEIPT_V09.json":"f0995dbec6d844fc3b32e05ac16381ea785079a3","SHARED_FOREST_TREE_SCAN_RECEIPT_V12.json":"800c307ea4cd09f179e1c24d591b50ab539ca4e5","WINDWAITING_CLIFF_AREA_ROUTE_CORRIDOR_V01.json":"7587e3f07934a885a1867716e9400bd599b528af","WINDWAITING_CLIFF_AREA_SPATIAL_CANDIDATE_V01.json":"81e14da2ebb23adc4bb6ac63691d8d5d6b85f617","WINDWAITING_CLIFF_CG_TRACE_GEOMETRY_AUDIT_V01.json":"17374a204b9a9e2c54248e57711d5f654a9364e8","WINDWAITING_CLIFF_CG_TRACE_V03.json":"0b96f5e44a9a2b0d5c9393d7be8b30bfcc449232","WINDWAITING_CLIFF_PROJECTED_ELEVATION_CONTROL_V01.json":"3dd7fb64e5de4006a57d286396f1499bf0045080","WINDWAITING_CLIFF_RENDER_MATCH_READINESS_V01.json":"b1153237958dba424b2ca60b88acf38bf08ad02b"};
const areaMaturity=levels=>Math.round(AREA_SNAPSHOT.stages.reduce((sum,s,i)=>sum+s[1]*levels[i],0)/5)*5;
function renderAreaProgress(parent){
 const section=node("section","");section.id="area-progress";section.className="area-progress";
 section.append(node("h3","8エリア｜制作到達度"),node("p","証跡確認日 "+AREA_SNAPSHOT.date+"。5%刻みの概算指標で、工数・完成面積・正式QAの割合ではありません。未確認は加点なし。局所成果は半分まで、全域で確認した工程のみ満点。過去の概算と、現在HEADで照合できた証跡の加点は別表示。"));
 const rubric=node("details","");rubric.append(node("summary","算出方法・工程配点"),node("p",AREA_SNAPSHOT.stages.map(([n,w])=>n+" "+w+"%").join(" ／ ")),node("p","各工程は未確認0、局所候補0.5、全域確認1。構想・範囲の満点は暫定8エリアの識別のみ。100%には全域のゲーム統合・独立QA・正式採用が必要。旧2D実装を新3D完成とはみなしません。"));section.append(rubric);
 const grid=node("div","");grid.className="area-progress-grid";
 for(const [id,name,levels,note,links,owners] of AREA_SNAPSHOT.areas){
  const card=node("article","");card.className="tile area-progress-card";card.dataset.areaId=id;
  const percent=areaMaturity(levels);card.append(node("h4",name),node("strong","約 "+percent+"%"));
  const bar=node("progress","");bar.max=100;bar.value=percent;bar.setAttribute("aria-label",name+"の概算制作到達度");card.append(bar,node("p",note));const current=node("p","現HEADの証跡加点：照合待ち");current.className="area-current-score";card.append(current);
  const fresh=node("p","証跡スナップショット／現在HEAD未照合");fresh.className="area-progress-freshness";fresh.dataset.owners=owners.join(",");card.append(fresh);
  const details=node("details","");details.append(node("summary","工程内訳・設計資料"));
  for(const [[label,weight],i] of AREA_SNAPSHOT.stages.map((x,i)=>[x,i]))details.append(node("p",label+"： "+(levels[i]===1?"全域確認":levels[i]===0.5?"局所候補・途中":"未確認")+"（"+(weight*levels[i])+"/"+weight+"）"));
  for(const [label,path,comment] of links){const link=node("a",label);link.href="https://github.com/"+repo+(typeof path==="number"?"/pull/"+path+"#issuecomment-"+comment:"/blob/"+AREA_SNAPSHOT.heads[482]+"/docs/production/region_master/"+path);link.rel="noopener noreferrer";details.append(link);}
  card.append(details);
  const components=node("details","");components.className="area-modules";components.append(node("summary","領域別進捗（"+AREA_MODULES[id].length+"項目）"));
  for(const [mi,m] of AREA_MODULES[id].entries()){
   const row=node("div","");row.className="area-module";row.dataset.moduleOwner=String(m.owner);row.dataset.moduleIndex=String(mi);row.dataset.verified="unknown";if(m.source){row.dataset.source=m.source;row.dataset.blob=m.blob;}
   const p=areaMaturity(m.levels);row.append(node("strong",m.name+" / "+(p?"約 "+p+"%":"未確認")),node("p",m.note));
   if(m.source||m.comment){const a=node("a","制作証跡");a.href="https://github.com/"+repo+(m.source?"/blob/"+AREA_SNAPSHOT.heads[482]+"/docs/production/region_master/"+m.source:"/pull/"+m.owner+"#issuecomment-"+m.comment);a.rel="noopener noreferrer";row.append(a);}
   const fresh=node("small","証跡照合待ち");fresh.className="module-evidence-status";row.append(fresh);components.append(row);
  }
  card.append(components);grid.append(card);
 }
 section.append(grid);
 const newEvidence=node("details","");newEvidence.id="area-new-evidence";newEvidence.append(node("summary","新しい設計・制作記録"),node("p","担当PRとの照合待ち"));section.append(newEvidence);
 const refreshEvidence=node("button","設計証跡を再照合");refreshEvidence.type="button";refreshEvidence.onclick=async()=>{refreshEvidence.disabled=true;try{const p=await read("/pulls/482");await reconcileAreaEvidence(p.head?.sha,true);}catch(e){const box=byId("area-new-evidence");if(box)box.append(node("p","再照合失敗： "+e.message+"／前回証跡を保持"));}finally{refreshEvidence.disabled=false;}};section.append(refreshEvidence);
 const common=node("details","");common.append(node("summary","共通設計資料・カテゴリ別データ"));
 const references=[["国土・エリア設計継続資料","IRELAND_COUNTRY_AREA_BLUEPRINT_CONTINUITY_V01.md"],["8エリア暫定平面図","RILDE_AREA_FIRST_PLAN_V03.svg"],["8エリア暫定平面データ","RILDE_AREA_FIRST_PLAN_V03.json"],["平面・縦横断面設計枠","RILDE_EIGHT_AREA_PLAN_SECTION_SLOTS_V01.svg"],["河川・水辺｜断面模式図","RILDE_C02_C03_SECTION_HYDROLOGY_V01.svg"],["河川・水辺｜断面データ","RILDE_C02_C03_SECTION_HYDROLOGY_V01.json"],["河川・水辺｜河川網V26","RILDE_C03_RIVER_NETWORK_DESIGN_V26.json"],["樹木｜V55素材来歴","MOSS_FOREST_HERO_TREE_SOURCE_RECEIPT_V55.json"],["植物・森林｜植生配置V09","MOSS_FOREST_A2_ECOLOGY_RELAYOUT_DESIGN_V09.json"],["遺跡｜V64設計記録","MOSS_FOREST_SMALL_RUINS_BLUEPRINT_RECEIPT_V64.json"],["全域｜接続・未確定項目","RILDE_EIGHT_AREA_INTERFACE_RECONCILIATION_V01.json"]];
 for(const [label,path] of references){const a=node("a",label);a.href="https://github.com/"+repo+"/blob/"+AREA_SNAPSHOT.heads[482]+"/docs/production/region_master/"+path;a.rel="noopener noreferrer";common.append(a);}
 section.append(common);parent.append(section);
}
function reconcileAreaProgress(pulls){
 if(!Array.isArray(pulls))return;
 for(const label of document.querySelectorAll(".area-progress-freshness")){
  const ids=label.dataset.owners.split(",").map(Number);const changed=[],missing=[];
  for(const id of ids){const p=pulls.find(x=>x.number===id);if(!p||!p.head?.sha)missing.push(id);else if(p.head.sha!==AREA_SNAPSHOT.heads[id])changed.push(id);}
  for(const row of label.closest(".area-progress-card").querySelectorAll(".area-module:not([data-source])")){
   const owner=Number(row.dataset.moduleOwner),p=pulls.find(x=>x.number===owner),status=row.querySelector(".module-evidence-status");
   const m=AREA_MODULES[label.closest(".area-progress-card").dataset.areaId][Number(row.dataset.moduleIndex)];row.dataset.verified=m.comment&&p?.head?.sha===AREA_SNAPSHOT.heads[owner]?"yes":"unknown";status.textContent=!m.comment?"制作証跡未確認":!p?.head?.sha?"担当HEAD未照合":p.head.sha===AREA_SNAPSHOT.heads[owner]?"担当HEAD一致":"担当更新／前回評価を保持";
  }
  label.textContent=changed.length?"新しいHEADあり： "+changed.map(x=>"#"+x).join("、")+"／概算は前回証跡（再評価要）":missing.length?"HEAD未照合： "+missing.map(x=>"#"+x).join("、")+"／概算は前回証跡":"担当HEAD一致／証跡スナップショット";
 }
 refreshCurrentAreaScores();
}
function refreshCurrentAreaScores(){for(const card of document.querySelectorAll(".area-progress-card")){const rows=[...card.querySelectorAll(".area-module")],valid=rows.filter(row=>row.dataset.verified==="yes"),out=card.querySelector(".area-current-score");if(!valid.length){out.textContent="現HEADの証跡加点：未照合";continue;}const modules=AREA_MODULES[card.dataset.areaId],levels=AREA_SNAPSHOT.stages.map((_,i)=>Math.max(0,...valid.map(row=>modules[Number(row.dataset.moduleIndex)].levels[i])));out.textContent="現HEADの照合済み証跡加点：約 "+areaMaturity(levels)+"%（"+valid.length+"/"+rows.length+"項目、未照合は加点なし）";}}
let areaEvidenceCache=null,areaEvidenceRequest=null,areaEvidenceGeneration=0;
function applyAreaEvidence(head,files){
 const indexed=new Map(files.map(f=>[f.name,f.sha]));
 for(const row of document.querySelectorAll(".area-module[data-source]")){
  const match=indexed.get(row.dataset.source)===row.dataset.blob;
  row.dataset.verified=match?"yes":"unknown";row.querySelector(".module-evidence-status").textContent=match?"現HEADで証跡一致":"証跡変更・欠落／前回評価を保持";
 }
 refreshCurrentAreaScores();
 const panel=byId("area-new-evidence");if(!panel)return;
 const extra=files.filter(f=>AREA_BASELINE_FILES[f.name]!==f.sha&&/^(RILDE_|MOSS_FOREST_|WINDWAITING_CLIFF_|SHARED_FOREST_|ALVERIA_)[A-Z0-9_]+\.json$/.test(f.name));
 panel.replaceChildren(node("summary","新規・更新された設計記録（"+extra.length+"件）"),node("p","現HEAD "+head.slice(0,12)+"。既知の証跡はファイルSHAで自動再照合し、現HEADの証跡加点を再計算。未審査の新規・変更資料は加点せず、工程評価の見直し対象にします。"));
 for(const f of extra.slice(0,30)){const a=node("a",f.name);a.href="https://github.com/"+repo+"/blob/"+head+"/docs/production/region_master/"+f.name;a.rel="noopener noreferrer";panel.append(a);}
 if(extra.length>30)panel.append(node("p","表示上限30件。全件は担当PRを確認。"));
}
async function reconcileAreaEvidence(head,force=false){
 if(!/^[a-f0-9]{40}$/.test(head||""))return;
 if(document.hidden&&!force)return;
 if(areaEvidenceRequest?.head===head)return areaEvidenceRequest.promise;
 const generation=++areaEvidenceGeneration;
 if(head===AREA_SNAPSHOT.heads[482]&&!force){areaEvidenceRequest=null;applyAreaEvidence(head,Object.entries(AREA_BASELINE_FILES).map(([name,sha])=>({name,sha})));return;}
 if(areaEvidenceCache?.head===head&&!force){areaEvidenceRequest=null;applyAreaEvidence(head,areaEvidenceCache.files);return;}
 for(const row of document.querySelectorAll(".area-module[data-source]")){row.dataset.verified="unknown";row.querySelector(".module-evidence-status").textContent="現HEAD照合中／前回評価を保持";}
 refreshCurrentAreaScores();
 const promise=(async()=>{try{
  const files=await read("/contents/docs/production/region_master?ref="+head);
  if(generation!==areaEvidenceGeneration)return;
  if(!Array.isArray(files)||files.length>1000||files.some(f=>!f||typeof f.name!=="string"||!/^[a-f0-9]{40}$/.test(f.sha||"")))throw Error("設計一覧形式不正");
  areaEvidenceCache={head,files:files.filter(f=>f.type==="file")};
  applyAreaEvidence(head,areaEvidenceCache.files);
 }catch(e){if(generation!==areaEvidenceGeneration)return;const panel=byId("area-new-evidence");if(panel)panel.replaceChildren(node("summary","新しい設計・制作記録（照合失敗）"),node("p",e.message+"／前回評価・資料リンクを保持"));}finally{if(areaEvidenceRequest?.generation===generation)areaEvidenceRequest=null;}})();
 areaEvidenceRequest={head,generation,promise};return promise;
}
window.addEventListener("studio-live-pulls",e=>{reconcileAreaProgress(e.detail);const p=Array.isArray(e.detail)?e.detail.find(x=>x.number===482):null;if(p)void reconcileAreaEvidence(p.head?.sha);});
async function loadAreaBlueprints(){
 const area=byId("area-blueprints"),status=byId("area-blueprints-status");
 if(!area||!status)return;
 area.replaceChildren();renderAreaProgress(area);status.textContent="担当PRを検索中";
 const designBranch="docs/ireland-world-source-grounded-plan-20261123";
 const designFiles=[
 ["物語接続図 v0.4（SVG・地理実測ではない）","docs/production/region_master/IRELAND_STORY_TOPOLOGY_V04.svg"],
 ["国土図面・入力資料契約 v0.4","docs/production/region_master/IRELAND_COUNTRY_DRAWING_SOURCE_CONTRACT_V04.md"],
 ["国土・エリア設計継続資料 v0.1","docs/production/region_master/IRELAND_COUNTRY_AREA_BLUEPRINT_CONTINUITY_V01.md"],
 ["Studio設計図候補インベントリ","docs/production/region_master/PRODUCTION_STUDIO_BLUEPRINT_CANDIDATES_V01.json"]
 ];
 const design=tile(area,"アイルランド国土・エリア設計（専用ブランチ）",["制作中 / 設計候補 / G1 BLOCKED","正式地形・完成図面ではありません"],[]);
 for(const [label,path] of designFiles){const link=node("a",label);link.href="https://github.com/"+repo+"/blob/"+designBranch+"/"+path;link.rel="noopener noreferrer";design.append(link);}
 const preview=node("figure","");
 preview.className="blueprint-preview";
 const image=node("img","");
 image.alt="物語接続図 v0.4（実測地形ではありません）";
 image.loading="lazy";
 image.width=1420;image.height=360;
 image.style.width="100%";image.style.height="auto";
 image.referrerPolicy="no-referrer";
 image.src="https://raw.githubusercontent.com/"+repo+"/83c612079128c308baf021ad22f53498ae611ecf/docs/production/region_master/IRELAND_STORY_TOPOLOGY_V04.svg";
 image.addEventListener("error",()=>{image.remove();preview.append(node("p","SVGプレビュー取得不可。上記の原本リンクから確認してください。"));});
 preview.append(image,node("figcaption","物語接続図 v0.4 / G1 BLOCKED / 設計候補（地理・寸法の実測図ではありません）"));
 design.append(preview);
 // Inventory mirrors the source-grounded continuity contract, not verified terrain.
 const areas=[
 ["RILDE_VILLAGE","リルド村","港・集落・河岸・建築接地","#364"],
 ["WINDWAITING_CLIFF","風待ちの崖","崖面・台地・地層・崩落・登攀","#421"],
 ["COASTAL_MEADOW","海岸草原","緩斜面・農地・生垣・排水","ECO/WORLD"],
 ["RIVER_CORRIDOR","河川回廊","縦断河床・流域・橋・護岸","WORLD/ROUTE"],
 ["MOSS_FOREST_A1","モスの森 A1","林縁・入口・探索経路","ECO/WORLD"],
 ["MOSS_FOREST_A2","モスの森 A2","谷・小川・林冠・障害物","ECO/WORLD"],
 ["MOSS_FOREST_A3","モスの森 A3","岩場・渓谷・砦への遷移","ECO/WORLD"],
 ["DUNVAR_FORTRESS","ドゥンヴァル砦","高地・進入路・基礎・排水","BUILD/WORLD"]
 ];
 const inventory=tile(area,"8エリア設計図インベントリ",["設計候補8件 / G1 BLOCKED / D1〜D4未完了","座標・標高・エリア境界・物理的な接続は未確定。物語接続と歩行可能経路は別管理。"],[]);
 const inventoryList=node("ul","");
 inventoryList.className="area-inventory";
 for(const [id,name,focus,owner] of areas){
  const item=node("li","");
  item.append(node("strong",name+" ("+id+")"),node("span","対象: "+focus+" / 担当調整: "+owner+" / 図面・実測: 未検証"));
  inventoryList.append(item);
 }
 inventory.append(inventoryList);
 const contract=node("a","エリア別設計図の要求仕様・未確定項目を確認");
 contract.href="https://github.com/"+repo+"/blob/"+designBranch+"/docs/production/region_master/IRELAND_COUNTRY_AREA_BLUEPRINT_CONTINUITY_V01.md";
 contract.rel="noopener noreferrer";inventory.append(contract);

 try{
  const found=new Map(),allPulls=[];
  for(let page=1;page<=3;page++){
   const pulls=await read("/pulls?state=open&per_page=100&page="+page);
   allPulls.push(...pulls);
   for(const p of pulls){
    const title=String(p.title||"");
    if(/(アイルランド|Ireland|Irish|地形|エリア設計|area.blueprint|terrain.blueprint|world.blueprint|地勢|地形設計)/i.test(title))found.set(p.number,p);
   }
   if(pulls.length<100)break;
  }
  reconcileAreaProgress(allPulls);
  const world=allPulls.find(p=>p.number===482);if(world)void reconcileAreaEvidence(world.head?.sha);
  const candidates=[...found.values()].sort((a,b)=>String(b.updated_at).localeCompare(String(a.updated_at)));
  for(const p of candidates){
   const card=tile(area,p.title,["PR #"+p.number+" / "+(p.draft?"Draft":"Open"),"HEAD: "+String(p.head?.sha||"未取得").slice(0,12),"更新: "+p.updated_at,"設計図の実ファイル・G1〜G4: 未検証"],[["担当PR・設計図資料","/pull/"+p.number]]);
   const state=node("p","現HEADのActions: 取得中");card.append(state);
   if(!p.head?.ref)continue;
   read("/actions/runs?branch="+encodeURIComponent(p.head.ref)+"&per_page=10").then(data=>{
    const run=(data.workflow_runs||[]).find(x=>x.head_sha===p.head.sha&&x.head_branch===p.head.ref);
    if(!run){state.textContent="現HEADのActions: 未検出";return;}
    state.textContent="現HEADのActions: "+run.name+" / "+run.status+" / "+(run.conclusion||"未確定");
    const button=node("button","設計図・レンダーのArtifactsを確認");button.type="button";button.addEventListener("click",()=>loadArtifacts(run,card,button));card.append(button);
   }).catch(e=>{state.textContent="Actions取得失敗: "+e.message;});
  }
  status.textContent=candidates.length+" 件の設計関連PR候補（タイトル検索・最大300件）"+(candidates.length?"":" / 未検出の場合は担当PRから確認");
 }catch(e){status.textContent="設計関連PR検索失敗: "+e.message;}
}

loadAreaBlueprints();

// Local-only image-space audit inspection. No upload, adoption or inferred world dimensions.
(() => {
 const area=byId("area-blueprints");
 const panel=node("article","");panel.className="tile";
 panel.append(node("h3","設計計測JSON・端末内検査"),node("p","崖CG輪郭・画像座標QA v01対応。取得済みJSONを端末内で読み取ります。原本の正当性やG1〜G4は独立検証しません。"));
 const label=node("label","計測JSONを選択");label.htmlFor="blueprint-audit-file";
 const file=node("input","");file.type="file";file.accept=".json,application/json";file.id="blueprint-audit-file";
 const result=node("div","未選択");result.id="blueprint-audit-result";result.setAttribute("role","status");
 panel.append(label,file,result);area.append(panel);
 let generation=0;
 file.addEventListener("change",async()=>{
  const current=++generation;result.replaceChildren();
  const selected=file.files[0];if(!selected){result.textContent="未選択";return;}
  try{
   if(selected.size>2*1024*1024)throw Error("2MB上限");
   const raw=await selected.text();if(current!==generation)return;
   const d=JSON.parse(raw);
   if(d?.schema!=="two.cliff.image_space_geometry_audit.v01"||!Array.isArray(d.derived)||d.derived.length>100||!d.qa||!d.checks)throw Error("非対応の計測JSON");
   if(!d.derived.every(x=>x&&typeof x.id==="string"&&Number.isFinite(x.polyline_length_px)&&x.polyline_length_px>=0&&Number.isSafeInteger(x.point_count)&&x.point_count>=0&&x.world_metric===null))throw Error("計測項目形式不正");
   const fmt=v=>v===null||v===undefined?"未記録":typeof v==="string"||typeof v==="number"||typeof v==="boolean"?String(v):"形式未対応";
   result.append(node("p","端末選択資料 / 来歴・SHA未検証 / 画像座標のみ（px）。実距離・標高・角度ではありません。"));
   result.append(node("p","点数: "+fmt(d.checks.point_count)+" / 特徴数: "+fmt(d.checks.feature_count)));
   result.append(node("p","比較準備: "+(d.comparison_ready===true?"資料申告：準備済み":"未完了")+" / "+fmt(d.reason)));
   for(const key of ["pixel_structure","source_trace_accuracy","projected_render_comparison","G1","G2","G3","G4"])result.append(node("p",key+": "+fmt(d.qa[key])+"（資料申告）"));
   const contract=d.required_render_contract||{};
   result.append(node("p","投影残差: "+fmt(contract.projected_residuals_px)+" / 許容誤差(px): "+fmt(contract.tolerance_px)+" / 不確かさ(px): "+fmt(contract.uncertainty_px)));
   for(const x of d.derived){const item=node("p",x.id+" / "+x.point_count+" 点 / 画像内輪郭長 "+x.polyline_length_px+" px / 実寸未確定");item.style.overflowWrap="anywhere";result.append(item);}
  }catch(e){if(current===generation)result.textContent="計測JSON検査失敗: "+e.message;}
 });
})();

// Placement proposals are local, reversible, and never overwrite an area source.
(() => {
 const ids=["RILDE_VILLAGE","WINDWAITING_CLIFF","COASTAL_MEADOW","RIVER_CORRIDOR","MOSS_FOREST_A1","MOSS_FOREST_A2","MOSS_FOREST_A3","DUNVAR_FORTRESS"];
 const names=["リルド村","風待ちの崖","海岸草原","河川回廊","モスの森 A1","モスの森 A2","モスの森 A3","ドゥンヴァル砦"];
 const schema="two.studio.provisional_placement.v1", source="300fa1fa080886abdb1493039a41fe6449633cb0";
 const panel=node("article","");panel.className="tile";panel.id="placement-editor";
 panel.append(node("h3","暫定エリア配置案"),node("p","端末内の配置案専用。X東・Y北・Z上（m）、Z軸回転は度・反時計回り。全体原点未確定。空欄は未設定であり0ではありません。地形・境界・原本には反映しません。"));
 const fields=["x_m","y_m","z_m","yaw_deg"],labels=["X 東 (m)","Y 北 (m)","Z 上 (m)","Z 回転 (°)"];
 let rows=ids.map(id=>({id,x_m:null,y_m:null,z_m:null,yaw_deg:null})), current=0, revision=0, generation=0;
 const choose=node("select","");choose.setAttribute("aria-label","配置エリア");ids.forEach((id,i)=>{const o=node("option",names[i]);o.value=String(i);choose.append(o);});panel.append(choose);
 const inputs=fields.map((key,i)=>{const l=node("label",labels[i]);const input=node("input","");input.type="number";input.step="any";input.min=key==="yaw_deg"?"-360":"-1000000";input.max=key==="yaw_deg"?"360":"1000000";input.style.maxWidth="100%";input.setAttribute("aria-label",labels[i]);l.append(input);panel.append(l);return input;});
 const status=node("p","");status.setAttribute("role","status");status.id="placement-status";
 const summary=node("ul","");summary.id="placement-summary";summary.className="area-inventory";
 const plot=document.createElementNS("http://www.w3.org/2000/svg","svg");plot.id="placement-overview";plot.setAttribute("viewBox","0 0 320 260");plot.setAttribute("role","img");plot.setAttribute("aria-label","暫定配置の俯瞰");plot.style.cssText="width:100%;height:auto;max-width:100%;display:block;background:#15231f;border-radius:8px";
 const plotNote=node("p","");plotNote.id="placement-overview-note";
 const svg=(tag,attrs,label)=>{const n=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(label!==undefined)n.textContent=label;plot.append(n);return n;};
 function overview(){
  plot.replaceChildren();
  const points=rows.map((r,i)=>({...r,i})).filter(r=>r.x_m!==null&&r.y_m!==null);
  svg("text",{x:12,y:16,fill:"#c4d5cc","font-size":10},"北 ↑ / 東 → · X/Y 同一縮尺");
  if(!points.length){svg("text",{x:160,y:130,fill:"#d4e3da","font-size":12,"text-anchor":"middle"},"X・Yの入力待ち");plotNote.textContent="配置点 0/8。未設定座標は描画しません。";return;}
  const minX=Math.min(...points.map(p=>p.x_m)),maxX=Math.max(...points.map(p=>p.x_m)),minY=Math.min(...points.map(p=>p.y_m)),maxY=Math.max(...points.map(p=>p.y_m));
  const scale=Math.min(248/Math.max(1,maxX-minX),176/Math.max(1,maxY-minY));
  const cx=(minX+maxX)/2,cy=(minY+maxY)/2;
  svg("rect",{x:36,y:34,width:248,height:176,fill:"none",stroke:"#506a60","stroke-dasharray":"3 4"});
  const groups=new Map();for(const p of points){const key=p.x_m+","+p.y_m;const list=groups.get(key)||[];list.push(p);groups.set(key,list);}
  for(const group of groups.values()){
   const p=group[0],x=160+(p.x_m-cx)*scale,y=122-(p.y_m-cy)*scale;
   for(const q of group){
    if(q.yaw_deg!==null){const a=q.yaw_deg*Math.PI/180;svg("line",{x1:x,y1:y,x2:x+16*Math.cos(a),y2:y-16*Math.sin(a),stroke:"#d4b879","stroke-width":2,"data-yaw-area":q.id});}
    svg("circle",{cx:x,cy:y,r:q.i===current?6:4,fill:q.i===current?"#e1bd79":"#8ccba4",stroke:"#15231f","data-area-id":q.id});
   }
   svg("text",{x,y:y-9,fill:"#e3eee7","font-size":10,"text-anchor":"middle"},group.map(q=>q.i+1).join("/"));
  }
  const raw=60/scale,base=Math.pow(10,Math.floor(Math.log10(raw))),length=[1,2,5].map(v=>v*base).filter(v=>v<=raw).pop()||base;
  svg("line",{x1:36,y1:235,x2:36+length*scale,y2:235,stroke:"#c4d5cc","stroke-width":2});
  svg("text",{x:36,y:250,fill:"#c4d5cc","font-size":10},Number(length.toPrecision(4))+" m");
  plotNote.textContent="配置点 "+points.length+"/8（番号は下の一覧）。同一点 "+[...groups.values()].filter(g=>g.length>1).length+" 箇所。地形・境界・接続・衝突は未検証。方向線はローカル+X軸の向き。";
 }
 const valid=(v,k)=>v===null||(typeof v==="number"&&Number.isFinite(v)&&Math.abs(v)<=(k==="yaw_deg"?360:1000000));
 // Manual, provisional anchor pair: never infer a physical connection from story adjacency.
 const anchorPanel=node("details","");anchorPanel.id="placement-anchor-check";
 anchorPanel.append(node("summary","接続アンカーの位置誤差検査"),node("p","対応する2点のエリア内ローカル座標を入力。単位m、配置案の平行移動とZ回転を適用。接続の正式採用・面の継ぎ目・衝突は判定しません。"));
 const anchorNumber=(parent,label,nonnegative=false)=>{const l=node("label",label),input=node("input","");input.type="number";input.step="any";input.min=nonnegative?"0":"-1000000";input.max="1000000";input.style.maxWidth="100%";input.setAttribute("aria-label",label);l.append(input);parent.append(l);return input;};
 const sides=["A","B"].map((side,i)=>{const group=node("fieldset","");group.style.minWidth="0";group.append(node("legend","アンカー "+side));const select=node("select","");select.setAttribute("aria-label","アンカー "+side+" エリア");ids.forEach((id,j)=>{const o=node("option",names[j]);o.value=String(j);select.append(o);});select.value=String(i);group.append(select);const xyz=["X","Y","Z"].map(axis=>anchorNumber(group,side+" local "+axis+" (m)"));anchorPanel.append(group);return {select,xyz};});
 const tolerance=anchorNumber(anchorPanel,"許容誤差 t (m)",true),uncertainty=anchorNumber(anchorPanel,"合成不確かさ u (m)",true);
 const anchorResult=node("div","");anchorResult.id="anchor-result";anchorResult.setAttribute("role","status");anchorPanel.append(anchorResult);
 const receiptButton=node("button","検査結果JSONを書き出す");receiptButton.type="button";receiptButton.disabled=true;
 const receiptLabel=node("label","検査結果JSONを再読込（入力値のみ復元・再計算）"),receiptFile=node("input","");receiptFile.type="file";receiptFile.accept=".json,application/json";receiptFile.id="anchor-receipt-import";receiptLabel.htmlFor=receiptFile.id;
 const receiptStatus=node("p","");receiptStatus.id="anchor-receipt-status";receiptStatus.setAttribute("role","status");
 anchorPanel.append(receiptButton,receiptLabel,receiptFile,receiptStatus);
 const receiptSchema="two.studio.anchor_residual_receipt.v1",coordinateContract={axes:"X east Y north Z up",unit:"metre",origin:null,yaw:"degrees_ccw_about_positive_z"};
 let receipt=null,receiptGeneration=0;
 function downloadReceipt(data,name){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=node("a","");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 receiptButton.onclick=()=>{if(!commit()||!receipt)return;downloadReceipt(receipt,"two-anchor-residual-r"+revision+".json");receiptStatus.textContent="端末内に書出し。共有は担当PR等の許可された経路で行ってください。";};
 receiptFile.addEventListener("change",async()=>{
  const g=++receiptGeneration,selected=receiptFile.files[0];if(!selected)return;
  try{
   if(selected.size>65536)throw Error("64KiB上限");
   const data=JSON.parse(await selected.text());if(g!==receiptGeneration)return;
   const indices=validateReceipt(data);
   if(pendingPlacement())throw Error("未反映の配置入力あり");
   sides.forEach((s,i)=>{s.select.value=String(indices[i]);s.xyz.forEach((input,j)=>input.value=String(data.anchors[i].local_xyz_m[j]));});
   tolerance.value=String(data.tolerance_m);uncertainty.value=String(data.uncertainty_m);anchors();
   receiptStatus.textContent="入力復元・再計算完了。保存された判定は信用せず再計算しました。";
  }catch(e){if(g===receiptGeneration)receiptStatus.textContent="検査結果読込失敗: "+e.message;}
 });
 function pendingPlacement(){return inputs.some((input,i)=>input.validity.badInput||(input.value===""?null:input.valueAsNumber)!==rows[current][fields[i]]);}
 function validateReceipt(data,compare=false){
   const cc=data?.coordinate_contract;
   if(data?.schema!==receiptSchema||data.status!=="PROVISIONAL"||data.source_blob!==source||!cc||Object.keys(coordinateContract).some(k=>cc[k]!==coordinateContract[k])||!Number.isSafeInteger(data.placement_revision)||data.placement_revision<0||(!compare&&data.placement_revision!==revision)||!Array.isArray(data.anchors)||data.anchors.length!==2)throw Error("検査契約・配置改訂不一致");
   const indices=data.anchors.map(a=>ids.indexOf(a?.area_id));
   if(indices.some(i=>i<0)||indices[0]===indices[1])throw Error("エリアID不正");
   const bounded=v=>typeof v==="number"&&Number.isFinite(v)&&Math.abs(v)<=1000000;
   if(!data.anchors.every((a,i)=>Array.isArray(a.local_xyz_m)&&a.local_xyz_m.length===3&&a.local_xyz_m.every(bounded)&&a.placement&&a.placement.id===a.area_id&&fields.every(k=>a.placement[k]!==null&&valid(a.placement[k],k)&&(compare||a.placement[k]===rows[indices[i]][k])))||![data.tolerance_m,data.uncertainty_m].every(v=>bounded(v)&&v>=0))throw Error("座標・配置スナップショット不一致");
  return indices;
 }
 function calculateAnchor(placements,local,t,u){
  const world=placements.map((p,i)=>{const [x,y,z]=local[i],a=p.yaw_deg*Math.PI/180;return [p.x_m+x*Math.cos(a)-y*Math.sin(a),p.y_m+x*Math.sin(a)+y*Math.cos(a),p.z_m+z];});
  const delta=world[1].map((v,i)=>v-world[0][i]),r=Math.hypot(...delta);
  const eps=64*Number.EPSILON*Math.max(1,...world.flat().map(Math.abs),r,t??0,u??0);
  const verdict=t===null||u===null?"BLOCKED":r+u<t-eps?"PASS":r-u>t+eps?"OUTSIDE":"HOLD";
  return {world,delta,r,eps,verdict};
 }
 const batch=node("details","");batch.id="anchor-batch";
 batch.append(node("summary","複数アンカー検査の一括比較"),node("p","同一配置案の検査JSONを最大32件・各64KiBまで選択。保存判定は採用せず再計算します。未反映入力は先に配置案へ反映してください。"));
 const batchLabel=node("label","検査JSONを複数選択"),batchInput=node("input","");batchInput.type="file";batchInput.multiple=true;batchInput.accept=".json,application/json";batchInput.id="anchor-batch-import";batchLabel.htmlFor=batchInput.id;
 const batchStatus=node("p","未選択");batchStatus.id="anchor-batch-status";batchStatus.setAttribute("role","status");
 const batchList=node("div","");batchList.id="anchor-batch-results";
 const compareLabel=node("label"," 基準JSONと現在配置を比較（異なる改訂を許可）"),compareMode=node("input","");compareMode.type="checkbox";compareMode.id="anchor-batch-compare";compareLabel.prepend(compareMode);
 const handoffButton=node("button","一括検査・修正候補JSONを書き出す");handoffButton.type="button";handoffButton.disabled=true;
 let batchReceipt=null;
 handoffButton.onclick=()=>{renderBatch();if(batchReceipt)downloadReceipt(batchReceipt,"two-anchor-handoff-r"+revision+".json");};
 batch.append(compareLabel,batchLabel,batchInput,batchStatus,handoffButton,batchList);anchorPanel.append(batch);
 compareMode.addEventListener("change",renderBatch);
 let batchItems=[],batchGeneration=0,batchLoading=false,batchError="";
 function renderBatch(){
  batchList.replaceChildren();batchReceipt=null;handoffButton.disabled=true;
  if(batchLoading){batchStatus.textContent="読込中";return;}
  if(batchError){batchStatus.textContent=batchError;return;}
  if(!batchItems.length){batchStatus.textContent="未選択";return;}
  if(pendingPlacement()){batchStatus.textContent="BLOCKED：未反映の配置入力あり";return;}
  const counts={PASS:0,HOLD:0,OUTSIDE:0,REJECTED:0},seen=new Set(),items=[];
  for(const item of batchItems){
   try{
    if(item.error)throw Error(item.error);
    const d=item.data,indices=validateReceipt(d,compareMode.checked),local=d.anchors.map(a=>a.local_xyz_m),placements=indices.map(i=>rows[i]);
    if(placements.some(p=>fields.some(k=>p[k]===null)))throw Error("現在配置のXYZ・回転が未設定");
    const baseline=compareMode.checked?calculateAnchor(d.anchors.map(a=>a.placement),local,d.tolerance_m,d.uncertainty_m):null;
    const key=JSON.stringify({pair:indices.map((i,j)=>[i,local[j]]).sort((a,b)=>a[0]-b[0]),t:d.tolerance_m,u:d.uncertainty_m,baseline:compareMode.checked?indices.map((i,j)=>[i,...fields.map(k=>d.anchors[j].placement[k])]).sort((a,b)=>a[0]-b[0]):null});
    if(seen.has(key))throw Error("同一入力の重複");seen.add(key);
    const result=calculateAnchor(placements,local,d.tolerance_m,d.uncertainty_m);
    counts[result.verdict]++;items.push({name:item.name,indices,result,baseline,baselineRevision:d.placement_revision,t:d.tolerance_m,u:d.uncertainty_m,local,placements:placements.map(p=>({...p})),baselinePlacements:baseline?d.anchors.map(a=>Object.fromEntries([["id",a.area_id],...fields.map(k=>[k,a.placement[k]])])):null});
   }catch(e){counts.REJECTED++;items.push({name:item.name,error:e.message});}
  }
  const rank={OUTSIDE:0,HOLD:1,PASS:2};
  // Rank by verdict, then conservative excess over tolerance (not raw distance).
  const excess=item=>item.result?item.result.r+item.u-item.t:0;
  items.sort((a,b)=>(rank[a.result?.verdict]??3)-(rank[b.result?.verdict]??3)||excess(b)-excess(a));
  const reportRows=[];
  for(const item of items){
   const line=node("article","");line.className="tile";line.dataset.verdict=item.result?.verdict??"REJECTED";line.append(node("strong",item.name));
   if(item.error){line.append(node("p","REJECTED： "+item.error));reportRows.push({file:item.name,verdict:"REJECTED",reason:item.error,action:"REVIEW_INPUT"});}
   else{const {r,verdict}=item.result,fmt=x=>Number(x.toPrecision(10)).toString();line.append(node("p",item.indices.map(i=>names[i]).join(" ↔ ")),node("p",verdict+" / r: "+fmt(r)+" m / t: "+fmt(item.t)+" m / u: "+fmt(item.u)+" m"));
    const action=verdict==="OUTSIDE"?"REVIEW_PLACEMENT":verdict==="HOLD"?"REMEASURE":"NO_POSITION_ACTION";
    const priority=verdict==="OUTSIDE"?1:verdict==="HOLD"?2:3;
    line.append(node("p","修正優先度 "+priority+" / 許容差上限との差 "+fmt(excess(item))+" m / "+(priority===1?"配置・接続点を確認":priority===2?"再計測":"位置検査のみ合格")));
    reportRows.push({file:item.name,area_ids:item.indices.map(i=>ids[i]),local_xyz_m:item.local,placement:item.placements,baseline_placement:item.baselinePlacements,baseline_revision:item.baseline?item.baselineRevision:null,tolerance_m:item.t,uncertainty_m:item.u,result:item.result,baseline_result:item.baseline,priority,action,upper_margin_m:excess(item)});
    if(item.baseline){const before=item.baseline,change=r-before.r,eps=before.eps+item.result.eps,uncertainty=2*item.u+eps;const trend=change>uncertainty?"増加":change< -uncertainty?"減少":"差を確定できない";line.dataset.trend=trend;line.append(node("p","基準 r"+item.baselineRevision+": "+before.verdict+" / "+fmt(before.r)+" m → 現在 r"+revision+": "+verdict+" / "+fmt(r)+" m"),node("p","残差差分: "+fmt(change)+" m / "+trend+"（同じ入力・t/u、差分不確かさ上限 2u）"));}
   }
   batchList.append(line);
  }
  batchReceipt={schema:"two.studio.anchor_batch_handoff.v1",status:"PROVISIONAL",source_blob:source,coordinate_contract:coordinateContract,placement_revision:revision,mode:compareMode.checked?"BASELINE_COMPARE":"STRICT",placement:rows.map(r=>({...r})),counts,items:reportRows,qa_scope:"MANUAL_INPUT_POSITION_ONLY",independent_qa:"NOT_RUN",assignment:"UNASSIGNED"};
  handoffButton.disabled=false;
  batchStatus.textContent=(compareMode.checked?"基準→現在の比較 / ":"厳密照合 / ")+"配置 revision "+revision+" / "+batchItems.length+" 件 / PASS "+counts.PASS+" / HOLD "+counts.HOLD+" / OUTSIDE "+counts.OUTSIDE+" / REJECTED "+counts.REJECTED+"（暫定位置検査のみ）";
 }
 batchInput.addEventListener("change",async()=>{
  const g=++batchGeneration,files=Array.from(batchInput.files);batchItems=[];batchError="";batchLoading=false;
  if(files.length>32){batchError="選択上限32件";renderBatch();return;}
  batchLoading=true;renderBatch();
  const next=await Promise.all(files.map(async file=>{try{if(file.size>65536)throw Error("64KiB上限");return {name:file.name,data:JSON.parse(await file.text())};}catch(e){return {name:file.name,error:e.message};}}));
  if(g!==batchGeneration)return;batchItems=next;batchLoading=false;renderBatch();
 });
 // Read-only pairing of CLI preflight report with exact original handoff bytes.
 const enginePanel=node("details","");enginePanel.id="anchor-engine-preflight";
 enginePanel.append(node("summary","エンジン連携の事前検証結果"),node("p","#522 の出力JSONと元の一括検査JSONを選択し、入力SHA-256を照合します。署名・実行来歴・native実測は証明しません。現在の編集内容とは独立したスナップショットです。"));
 const engineFile=(id,label)=>{const l=node("label",label),i=node("input","");i.type="file";i.accept=".json,application/json";i.id=id;l.htmlFor=id;enginePanel.append(l,i);return i;};
 const engineOriginal=engineFile("engine-handoff-original","元の一括検査JSON"),engineReport=engineFile("engine-preflight-report","事前検証の出力JSON");
 const engineStatus=node("p","未照合");engineStatus.id="engine-preflight-status";engineStatus.setAttribute("role","status");
 const engineList=node("div","");engineList.id="engine-preflight-results";enginePanel.append(engineStatus,engineList);panel.append(enginePanel);
 let engineGeneration=0;
 async function readEngineReport(){
  const g=++engineGeneration;engineList.replaceChildren();engineStatus.textContent="未照合";
  const original=engineOriginal.files[0],report=engineReport.files[0];if(!original||!report)return;
  engineStatus.textContent="照合中";
  try{
   if(original.size>524288||report.size>524288)throw Error("各512KiB上限");
   const [raw,reportText]=await Promise.all([original.arrayBuffer(),report.text()]);
   const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",raw)),v=>v.toString(16).padStart(2,"0")).join("");
   if(g!==engineGeneration)return;
   const d=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw)),p=JSON.parse(reportText);
   if(d?.schema!=="two.studio.anchor_batch_handoff.v1"||d.status!=="PROVISIONAL"||d.source_blob!==source||!d.coordinate_contract||Object.keys(coordinateContract).some(k=>d.coordinate_contract[k]!==coordinateContract[k])||!Number.isSafeInteger(d.placement_revision)||d.placement_revision<0||!Array.isArray(d.items)||d.items.length<1||d.items.length>32)throw Error("元ファイル契約不一致");
   if(p?.schema!=="two.studio.anchor_handoff_preflight.v1"||p.source_blob!==source||p.input_sha256!==hash||p.placement_revision!==d.placement_revision||p.factory_ready!==false||p.native_observation!==false||p.independent_qa!=="NOT_RUN"||!Array.isArray(p.items)||p.items.length!==d.items.length)throw Error("事前検証契約・入力SHA不一致");
   const staged=[];
   for(let j=0;j<p.items.length;j++){
    const item=p.items[j];if(!item||item.index!==j)throw Error("項目番号不一致");
    const tile=node("article","");tile.className="tile";
    tile.append(node("strong","項目 "+(j+1)));
    if(item.verdict==="REJECTED"){if(item.action!=="REVIEW_INPUT"||typeof item.reason!=="string")throw Error("拒否項目形式不正");tile.append(node("p","REJECTED / "+item.reason.slice(0,240)));staged.push(tile);continue;}
    const result=item.result;
    if(item.evidence_class!=="PROVISIONAL_DESIGN"||typeof item.claimed_result_matches!=="boolean"||!Array.isArray(item.area_ids)||item.area_ids.length!==2||item.area_ids[0]===item.area_ids[1]||!item.area_ids.every(id=>ids.includes(id))||!result||!["PASS","HOLD","OUTSIDE"].includes(result.verdict)||!Number.isFinite(result.r)||result.r<0||!Number.isFinite(item.tolerance_m)||item.tolerance_m<0||!Number.isFinite(item.uncertainty_m)||item.uncertainty_m<0)throw Error("事前検証項目形式不正");
    const action=item.claimed_result_matches?{PASS:"NO_POSITION_ACTION",HOLD:"REMEASURE",OUTSIDE:"REVIEW_PLACEMENT"}[result.verdict]:"REVIEW_INPUT";
    if(item.action!==action)throw Error("修正候補の状態不一致");
    tile.append(node("p",item.area_ids.map(id=>names[ids.indexOf(id)]).join(" ↔ ")),node("p","出力申告: "+result.verdict+" / r "+result.r+" m / t "+item.tolerance_m+" m / u "+item.uncertainty_m+" m"),node("p",action+" / "+(item.claimed_result_matches?"保存判定一致（申告）":"保存判定不一致・入力確認")));
    staged.push(tile);
   }
   engineStatus.textContent="入力SHA-256一致 / revision "+p.placement_revision+" / "+p.items.length+" 件。出力の実行来歴は未認証。Factory BLOCKED / native観測なし / 独立QA NOT_RUN";
   engineList.append(node("p","入力SHA-256: "+hash),...staged);
  }catch(e){if(g===engineGeneration){engineList.replaceChildren();engineStatus.textContent="照合失敗: "+e.message;}}
 }
 engineOriginal.addEventListener("change",readEngineReport);engineReport.addEventListener("change",readEngineReport);
 for(const input of inputs)input.addEventListener("input",renderBatch);
 function numberFrom(input){return input.value!==""&&!input.validity.badInput&&input.validity.valid&&Number.isFinite(input.valueAsNumber)?input.valueAsNumber:null;}
 function anchors(){
  anchorResult.replaceChildren();delete anchorResult.dataset.verdict;receipt=null;receiptButton.disabled=true;receiptStatus.textContent="";
  const indices=sides.map(s=>Number(s.select.value));
  if(indices[0]===indices[1]){anchorResult.textContent="別の2エリアを選択してください。";return;}
  const local=sides.map(s=>s.xyz.map(numberFrom));
  const placements=indices.map(i=>rows[i]);
  if(local.some(v=>v.some(x=>x===null))||placements.some(p=>fields.some(k=>p[k]===null))){anchorResult.textContent="BLOCKED：両方の配置XYZ・回転とローカルアンカーXYZが必要です。";return;}
  const t=numberFrom(tolerance),u=numberFrom(uncertainty),{world,delta,r,eps,verdict}=calculateAnchor(placements,local,t,u);
  const fmt=x=>Number(x.toPrecision(10)).toString();
  anchorResult.append(node("p","配置 revision "+revision+" / A: "+world[0].map(fmt).join(", ")+" m / B: "+world[1].map(fmt).join(", ")+" m"),node("p","差分 B−A: "+delta.map(fmt).join(", ")+" m / 3D残差 r: "+fmt(r)+" m"));
  if(t===null||u===null){anchorResult.append(node("p","BLOCKED：許容誤差・合成不確かさを入力してください。"));return;}
  // Roundoff guard conservatively holds near the decision boundary.
  anchorResult.dataset.verdict=verdict;
  receipt={schema:receiptSchema,status:"PROVISIONAL",source_blob:source,coordinate_contract:coordinateContract,placement_revision:revision,anchors:placements.map((p,i)=>({area_id:p.id,placement:{...p},local_xyz_m:local[i],world_xyz_m:world[i]})),delta_b_minus_a_m:delta,residual_m:r,tolerance_m:t,uncertainty_m:u,roundoff_guard_m:eps,verdict,qa_scope:"MANUAL_INPUT_POSITION_ONLY",independent_qa:"NOT_RUN"};
  receiptButton.disabled=false;
  anchorResult.append(node("p",verdict+"（入力値に対する暫定位置検査のみ） / r+u="+fmt(r+u)+" m / r−u="+fmt(r-u)+" m / t="+fmt(t)+" m"),node("p","境界付近は丸め誤差を考慮してHOLD。入力不確かさは独立検証されていません。G1〜G4とは別判定です。"));
 }
 for(const input of [...sides.flatMap(s=>[s.select,...s.xyz]),tolerance,uncertainty])input.addEventListener("input",anchors);

 function render(){summary.replaceChildren();rows.forEach((r,i)=>{const l=node("li",(i+1)+". "+names[i]+": "+fields.map(k=>r[k]===null?"未設定":String(r[k])).join(" / "));summary.append(l);});status.textContent="配置案 revision "+revision+" / "+rows.filter(r=>fields.every(k=>r[k]!==null)).length+"/8 エリア入力済み / PROVISIONAL・未検証";overview();anchors();renderBatch();}
 function show(){inputs.forEach((input,i)=>input.value=rows[current][fields[i]]??"");render();}
 function commit(){const vals=inputs.map(input=>input.value===""?null:input.valueAsNumber);if(inputs.some(input=>input.validity.badInput)||vals.some((v,i)=>!valid(v,fields[i]))){status.textContent="入力範囲外または不正値。配置案は変更していません。";return false;}if(vals.some((v,i)=>v!==rows[current][fields[i]])){fields.forEach((k,i)=>rows[current][k]=vals[i]);revision++;}render();return true;}
 choose.addEventListener("change",()=>{if(!commit()){choose.value=String(current);return;}current=Number(choose.value);show();});
 const apply=node("button","配置案に反映");apply.type="button";apply.onclick=()=>commit();
 const exportButton=node("button","配置案JSONを書き出す");exportButton.type="button";exportButton.onclick=()=>{if(!commit())return;const data={schema,status:"PROVISIONAL",source_blob:source,coordinate_contract:{axes:"X east Y north Z up",unit:"metre",origin:null,yaw:"degrees_ccw_about_positive_z"},revision,areas:rows};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=node("a","");a.href=url;a.download="two-provisional-placement-r"+revision+".json";document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 const label=node("label","配置案JSONを読み込む");const file=node("input","");file.type="file";file.accept=".json,application/json";file.id="placement-import";label.htmlFor=file.id;
 file.addEventListener("change",async()=>{const g=++generation, selected=file.files[0];if(!selected)return;try{if(selected.size>65536)throw Error("64KiB上限");const data=JSON.parse(await selected.text());if(g!==generation)return;const c=data?.coordinate_contract;if(data?.schema!==schema||data.status!=="PROVISIONAL"||data.source_blob!==source||c?.axes!=="X east Y north Z up"||c.unit!=="metre"||c.origin!==null||c.yaw!=="degrees_ccw_about_positive_z"||!Number.isSafeInteger(data.revision)||data.revision<0||data.revision>=Number.MAX_SAFE_INTEGER-1||!Array.isArray(data.areas)||data.areas.length!==ids.length||!ids.every(id=>data.areas.filter(r=>r?.id===id).length===1))throw Error("配置契約・参照元不一致");const next=ids.map(id=>{const r=data.areas.find(x=>x.id===id);if(!fields.every(k=>valid(r[k],k)))throw Error("座標形式不正");return Object.fromEntries([["id",id],...fields.map(k=>[k,r[k]])]);});rows=next;revision=data.revision;show();}catch(e){if(g===generation)status.textContent="配置案読込失敗: "+e.message;}});
 panel.append(apply,exportButton,label,file,status,plot,plotNote,summary,anchorPanel);
 const link=node("a","設計担当PR #482・原本確認");link.href="https://github.com/"+repo+"/pull/482";panel.append(link);byId("area-blueprints").append(panel);show();
})();

const imageUrls=[];
function clearGallery(){for(const url of imageUrls)URL.revokeObjectURL(url);imageUrls.length=0;byId("gallery").replaceChildren();byId("images").value="";byId("image-status").textContent="画像未選択";}
byId("clear-images").addEventListener("click",clearGallery);
byId("images").addEventListener("change",()=>{const selected=Array.from(byId("images").files);clearGallery();let skipped=0;for(const file of selected){if(!["image/jpeg","image/png"].includes(file.type)||file.size>25*1024*1024||imageUrls.length>=24){skipped++;continue;}const url=URL.createObjectURL(file);imageUrls.push(url);const figure=node("figure","");figure.className="tile";const img=node("img","");img.src=url;img.alt=file.name;img.loading="lazy";img.addEventListener("error",()=>{img.remove();figure.append(node("p","画像を読み込めません"));});figure.append(img,node("figcaption",file.name),node("p","端末選択画像・来歴／SHA未検証"));byId("gallery").append(figure);}byId("image-status").textContent=imageUrls.length+" 件選択 / "+skipped+" 件除外（最大24件・各25MB）";});
window.addEventListener("pagehide",clearGallery);

async function loadArtifacts(run,card,button){
 button.disabled=true;card.querySelector(".artifact-results")?.remove();const area=node("div","取得中");area.className="artifact-results";area.setAttribute("role","status");card.append(area);
 try{const data=await read("/actions/runs/"+Number(run.id)+"/artifacts?per_page=100");area.replaceChildren();area.append(node("p","取得 "+data.artifacts.length+" / "+data.total_count+" 件（最大100件）"));
 for(const a of data.artifacts){tile(area,a.name,["Artifact ID: "+a.id,"生成HEAD: "+run.head_sha,"期限: "+a.expires_at,a.expired?"期限切れ":"未期限切れ",a.digest?"配布元digest: "+a.digest:"配布元digest未取得","ダウンロード内容・SHA照合未実施"],a.expired?[]:[["GitHubで取得（ログインが必要な場合あり）","/actions/runs/"+run.id+"/artifacts/"+a.id]]);}
 }catch(e){area.textContent="取得失敗: "+e.message;button.disabled=false;}
}
