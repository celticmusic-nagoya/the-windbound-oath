"use strict";
const repo="celticmusic-nagoya/the-windbound-oath", api="https://api.github.com/repos/"+repo;
const targets=[[427,"モルウェン"],[421,"風待ちの崖"],[364,"リルド村"]];
const byId=id=>document.getElementById(id);
function node(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
function tile(parent,title,lines,links=[]){const e=node("article","");e.className="tile";e.append(node("h3",title));for(const line of lines)e.append(node("p",line));for(const [label,path] of links){const a=node("a",label);a.href="https://github.com/"+repo+path;a.rel="noopener noreferrer";e.append(a);}parent.append(e);return e;}
async function read(path){const r=await fetch(api+path,{headers:{"Accept":"application/vnd.github+json"},credentials:"omit",cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);return r.json();}
async function refresh(){const button=byId("refresh");button.disabled=true;byId("status").textContent="取得中";for(const id of ["summary","projects","runs"])byId(id).replaceChildren();try{const results=await Promise.allSettled([...targets.map(([n])=>read("/pulls/"+n)),read("/actions/runs?per_page=20")]);let open=0,known=0;targets.forEach(([n,name],i)=>{const r=results[i];if(r.status==="fulfilled"){known++;const p=r.value;if(p.state==="open")open++;const card=tile(byId("projects"),name,["PR #"+n+" / "+(p.merged?"merged":p.state)+(p.draft?" / Draft":""),"HEAD: "+p.head.sha.slice(0,12),"更新: "+p.updated_at,"G1〜G4: 未取得（CI成功≠美術QA）"],[["担当PR","/pull/"+n]]);const recent=node("p","制作中のActions・成果物: 取得中");recent.setAttribute("role","status");card.append(recent);if(p.head?.ref&&/^[a-zA-Z0-9._/-]+$/.test(p.head.ref)){read("/actions/runs?branch="+encodeURIComponent(p.head.ref)+"&per_page=5").then(data=>{const runs=(data.workflow_runs||[]).filter(x=>x.head_branch===p.head.ref&&x.head_sha===p.head.sha);const run=runs[0];if(!run){recent.textContent="現HEADのActions: 未検出（過去の成果物は担当PRを参照）";return;}recent.textContent="現HEADのActions: "+run.name+" / "+run.status+" / "+(run.conclusion||"未確定");const link=node("a","制作中のActions・Artifactsを見る");link.href="https://github.com/"+repo+"/actions/runs/"+run.id;link.rel="noopener noreferrer";card.append(link);const button=node("button","このrunの成果物一覧");button.type="button";button.addEventListener("click",()=>loadArtifacts(run,card,button));card.append(button);}).catch(e=>{recent.textContent="現HEADのActions取得失敗: "+e.message;});}else recent.textContent="担当ブランチ未取得";}else tile(byId("projects"),name,["取得失敗 / "+r.reason.message],[["担当PR","/pull/"+n]]);});tile(byId("summary"),"担当PR",["取得 "+known+" / "+targets.length,"Open "+open+"（取得分のみ）"]);const ar=results[targets.length];if(ar.status==="fulfilled"){const runs=ar.value.workflow_runs;tile(byId("summary"),"Actions（最新20件）",["実行中 "+runs.filter(x=>x.status==="in_progress").length,"待機 "+runs.filter(x=>x.status==="queued"||x.status==="waiting").length]);for(const r of runs){const card=tile(byId("runs"),r.name,[r.status+" / "+(r.conclusion||"未確定"),r.head_branch+" / "+r.head_sha.slice(0,12),r.updated_at],[["実行詳細・Artifacts","/actions/runs/"+r.id]]);const button=node("button","成果物一覧を取得");button.type="button";button.addEventListener("click",()=>loadArtifacts(r,card,button));card.append(button);}}else tile(byId("runs"),"取得失敗",[ar.reason.message],[["Actions一覧","/actions"]]);byId("status").textContent=(results.every(r=>r.status==="fulfilled")?"取得完了":"一部取得失敗")+" / "+new Date().toLocaleString("ja-JP");}catch(e){byId("status").textContent="取得失敗: "+e.message;}finally{button.disabled=false;}}
byId("refresh").addEventListener("click",refresh);refresh();

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
 const valid=(v,k)=>v===null||(typeof v==="number"&&Number.isFinite(v)&&Math.abs(v)<=(k==="yaw_deg"?360:1000000));
 function render(){summary.replaceChildren();rows.forEach((r,i)=>{const l=node("li",names[i]+": "+fields.map(k=>r[k]===null?"未設定":String(r[k])).join(" / "));summary.append(l);});status.textContent="配置案 revision "+revision+" / "+rows.filter(r=>fields.every(k=>r[k]!==null)).length+"/8 エリア入力済み / PROVISIONAL・未検証";}
 function show(){inputs.forEach((input,i)=>input.value=rows[current][fields[i]]??"");render();}
 function commit(){const vals=inputs.map(input=>input.value===""?null:input.valueAsNumber);if(inputs.some(input=>input.validity.badInput)||vals.some((v,i)=>!valid(v,fields[i]))){status.textContent="入力範囲外または不正値。配置案は変更していません。";return false;}if(vals.some((v,i)=>v!==rows[current][fields[i]])){fields.forEach((k,i)=>rows[current][k]=vals[i]);revision++;}render();return true;}
 choose.addEventListener("change",()=>{if(!commit()){choose.value=String(current);return;}current=Number(choose.value);show();});
 const apply=node("button","配置案に反映");apply.type="button";apply.onclick=()=>commit();
 const exportButton=node("button","配置案JSONを書き出す");exportButton.type="button";exportButton.onclick=()=>{if(!commit())return;const data={schema,status:"PROVISIONAL",source_blob:source,coordinate_contract:{axes:"X east Y north Z up",unit:"metre",origin:null,yaw:"degrees_ccw_about_positive_z"},revision,areas:rows};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=node("a","");a.href=url;a.download="two-provisional-placement-r"+revision+".json";document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 const label=node("label","配置案JSONを読み込む");const file=node("input","");file.type="file";file.accept=".json,application/json";file.id="placement-import";label.htmlFor=file.id;
 file.addEventListener("change",async()=>{const g=++generation, selected=file.files[0];if(!selected)return;try{if(selected.size>65536)throw Error("64KiB上限");const data=JSON.parse(await selected.text());if(g!==generation)return;const c=data?.coordinate_contract;if(data?.schema!==schema||data.status!=="PROVISIONAL"||data.source_blob!==source||c?.axes!=="X east Y north Z up"||c.unit!=="metre"||c.origin!==null||c.yaw!=="degrees_ccw_about_positive_z"||!Number.isSafeInteger(data.revision)||data.revision<0||data.revision>=Number.MAX_SAFE_INTEGER-1||!Array.isArray(data.areas)||data.areas.length!==ids.length||!ids.every(id=>data.areas.filter(r=>r?.id===id).length===1))throw Error("配置契約・参照元不一致");const next=ids.map(id=>{const r=data.areas.find(x=>x.id===id);if(!fields.every(k=>valid(r[k],k)))throw Error("座標形式不正");return Object.fromEntries([["id",id],...fields.map(k=>[k,r[k]])]);});rows=next;revision=data.revision;show();}catch(e){if(g===generation)status.textContent="配置案読込失敗: "+e.message;}});
 panel.append(apply,exportButton,label,file,status,summary);
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
