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
