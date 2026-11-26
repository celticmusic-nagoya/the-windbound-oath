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
async function loadAreaBlueprints(){
 const area=byId("area-blueprints"),status=byId("area-blueprints-status");
 if(!area||!status)return;
 area.replaceChildren();status.textContent="担当PRを検索中";
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
  const found=new Map();
  for(let page=1;page<=3;page++){
   const pulls=await read("/pulls?state=open&per_page=100&page="+page);
   for(const p of pulls){
    const title=String(p.title||"");
    if(/(アイルランド|Ireland|Irish|地形|エリア設計|area.blueprint|terrain.blueprint|world.blueprint|地勢|地形設計)/i.test(title))found.set(p.number,p);
   }
   if(pulls.length<100)break;
  }
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
