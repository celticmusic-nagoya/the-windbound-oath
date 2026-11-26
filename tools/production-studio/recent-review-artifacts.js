"use strict";
(() => {
const REPO="celticmusic-nagoya/the-windbound-oath";
const GH="https://github.com/"+REPO, API="https://api.github.com/repos/"+REPO;
const HOME="feature/lind-village-world-integration-plan-01";
const CLIFF="feature/lind-cliff-rock-art-study-20261118";
const RULES=[
 ["main",/^morwen-isolated-vroid-reopen-review$/,"モルウェン・顔／髪","mouth-before.png,mouth-after.png,mouth-reopened.png,hair-before-selected.png,hair-after-selected.png,reopened-geometry.png,view-isolated-reopen-,rear-calibration-"],
 ["main",/^morwen-parallel-(?:A-face-body|B-hair|C-wardrobe)$/,"モルウェン・並列制作","mouth-,hair-,skirt-template.png,skirt-texture-editor.png,skirt-export-complete.png"],
 ["asset/morwen-measured-textile-20261125",/^morwen-measured-textile-not-adopted$/,"モルウェン・衣装","comparison.png,plaid_accent.png,dark_pleat.png"],
 ["feature/morwen-artdirected-sculpt-20261119",/^morwen-/,"モルウェン・造形",""],
 [HOME,/^aidan-measured-blueprint$/,"設計図・エイダン家","exterior-,interior-"],
 [HOME,/^(?:home-blueprint-batch-|aidan-interior-|home-cross-run-qa-|lind-home-os-isolated-|isolated-bed-drape-)/,"リルド村・エイダン家",""],
 ["feature/lind-home-01",/^(?:home|aidan|lind-home)/i,"リルド村・エイダン家",""],
 ["feature/lind-buildings-01",/^(?:lind|rild|building)/i,"リルド村・建築",""],
 [CLIFF,/^(?:c11-|lind-cliff|windwaiting)/i,"風待ちの崖",""],
 ["feature/lind-ecology-01",/^lind-eco-(?:53-candidate-evidence|integration-v2-package)$/,"リルド村・植生","eco_,renders/"],
 ["asset/morwen-measured-textile-20261125",/^morwen-(?:photo-textile-comparison|brass-source-maps|met-gold-thread-oa-sources)-not-adopted$/,"モルウェン・材質研究",""],
 ["infra/native-env-qualification-20261123",/^two-hairharpy-volume-/,"モルウェン・ヘア技術",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:hero-tree-v\d+-island-source|forest-v\d+-native-virtual-qa)$/,"世界・樹木／森林",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^(?:ireland|two-shared|lind|world|area)/i,"地図・エリア設計",""],
 ["feature/studio-sync-coverage-20261125",/^studio-sync-preview$/,"内部ギャラリー履歴","published/"],
];
const CATEGORIES=[...new Set(RULES.map(r=>r[2]))];
const SOURCE_LINKS=[
 ["リルド村・植生","/pull/357"],
 ["モルウェン・材質研究","/pull/540"],
 ["モルウェン・顔／髪","/pull/427"],
 ["風待ちの崖","/pull/421"],
 ["リルド村・エイダン家","/pull/364"],
 ["世界・樹木／森林","/pull/482"],
 ["地図・エリア設計","/pull/482"]
];
const isId=n=>Number.isSafeInteger(n)&&n>0;
const REFRESH_MS=5*60*1000, RETRY_MS=15*60*1000;
const PRESERVATION_WORKFLOW=".github/workflows/public-preservation-pilot.yml";
const preservationLabel=id=>[45706894871,45712121342,45717409074,45721456382].includes(id)?"自動保全":[45710690152,45713758086,45717635993,45722898390].includes(id)?"独立復元":"保全／復元（実行種別はログ参照）";
function selectPreservationRuns(data){
 if(!Array.isArray(data?.workflow_runs))throw Error("保全Actions一覧形式不正");
 const seen=new Set(),rows=[];
 for(const x of data.workflow_runs.slice(0,10)){
  if(!isId(x?.id)||seen.has(x.id)||x.path!==PRESERVATION_WORKFLOW||x.head_branch!=="main"||
     x.repository?.full_name!==REPO||x.head_repository?.full_name!==REPO||
     !/^[a-f0-9]{40}$/.test(x.head_sha||"")||!Number.isFinite(Date.parse(x.updated_at))||
     !["queued","waiting","pending","requested","in_progress","completed"].includes(x.status))continue;
  seen.add(x.id);
  rows.push({id:x.id,label:preservationLabel(x.id),status:x.status,conclusion:typeof x.conclusion==="string"?x.conclusion:null,updated:x.updated_at});
 }
 return rows.sort((a,b)=>Date.parse(b.updated)-Date.parse(a.updated)||b.id-a.id).slice(0,5);
}
function refreshDelay(success){return success?REFRESH_MS:RETRY_MS;}
function selectRecentArtifacts(data,category=""){
 if(!Array.isArray(data?.artifacts))throw Error("Artifact一覧形式不正");
 const seen=new Set(), rows=[];
 for(const a of data.artifacts.slice(0,100)){
  const w=a?.workflow_run;
  if(!isId(a?.id)||seen.has(a.id)||!isId(w?.id)||typeof a.name!=="string"||
     typeof w.head_branch!=="string"||!/^[a-f0-9]{40}$/.test(w.head_sha||"")||
     !isId(w.repository_id)||w.repository_id!==w.head_repository_id||
     a.expired!==false||!isId(a.size_in_bytes)||!Number.isFinite(Date.parse(a.created_at)))continue;
  const rule=RULES.find(([branch,pattern])=>w.head_branch===branch&&pattern.test(a.name));
  if(!rule||(category&&rule[2]!==category))continue;
  seen.add(a.id);
  rows.push({id:a.id,run:w.id,name:a.name,head:w.head_sha,category:rule[2],filter:rule[3],
    created:a.created_at,expires:a.expires_at||"",bytes:a.size_in_bytes,
    digest:/^sha256:[a-f0-9]{64}$/.test(a.digest||"")?a.digest:""});
 }
 return rows.sort((a,b)=>Date.parse(b.created)-Date.parse(a.created)||b.id-a.id).slice(0,30);
}
if(typeof module!=="undefined")module.exports={selectRecentArtifacts,selectPreservationRuns,refreshDelay};
if(typeof document==="undefined")return;
const area=document.getElementById("recent-review-artifacts"),status=document.getElementById("recent-review-status"),refresh=document.getElementById("refresh-recent-review");
if(!area||!status||!refresh)return;
const make=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;};
const heading=document.getElementById("recent-review-title");
const preservationHeading=make("h2","原本保全・独立復元｜公開Actions");
preservationHeading.id="preservation-status-title";
const preservationStatus=make("p","未取得");preservationStatus.setAttribute("role","status");
const preservationArea=make("section","");preservationArea.className="grid";
preservationArea.setAttribute("aria-labelledby",preservationHeading.id);
heading.before(preservationHeading,make("p","実行結果のみ表示。非公開原本・保全台帳・認証情報は取得しません。保存成功は正式採用やGUI再読込の証明ではありません。"),preservationStatus,preservationArea);
const cadence=make("p","表示中は5分ごとに自動更新。通信失敗時は15分間隔に抑制し、前回の結果を保持します。");
cadence.className="note";
const categoryLabel=make("label","制作領域で絞り込み");
const categorySelect=make("select","");categorySelect.id="recent-review-category";categoryLabel.htmlFor=categorySelect.id;
for(const name of ["",...CATEGORIES]){const option=make("option",name||"すべての制作領域");option.value=name;categorySelect.append(option);}
categorySelect.value="";
const sources=make("p","過去の成果物・一覧未検出時： ");sources.className="note";
for(const [name,path] of SOURCE_LINKS){const link=make("a",name+" / 担当PR");link.href=GH+path;link.rel="noopener noreferrer";sources.append(link,make("span","　"));}
refresh.after(cadence,categoryLabel,categorySelect,sources);
let generation=0,timer=null,nextDue=0,busy=false,snapshot=null,lastSuccess="",lastError="";
function schedule(){
 if(timer!==null)clearTimeout(timer);
 timer=null;
 if(!document.hidden&&!busy)timer=setTimeout(()=>update(),Math.max(0,nextDue-Date.now()));
}
async function publicJson(path){
 const res=await fetch(API+path,{credentials:"omit",cache:"no-store",signal:AbortSignal.timeout(10000),headers:{Accept:"application/vnd.github+json"}});
 if(!res.ok)throw Error("HTTP "+res.status);
 return res.json();
}
async function updatePreservation(){
 try{
  const rows=selectPreservationRuns(await publicJson("/actions/workflows/public-preservation-pilot.yml/runs?branch=main&per_page=10"));
  preservationArea.replaceChildren();
  for(const x of rows){
   const card=make("article","");card.className="tile";card.dataset.runId=String(x.id);
   card.append(make("h3",x.label),make("p",x.status+" / "+(x.conclusion||"未確定")),make("p",new Date(x.updated).toLocaleString("ja-JP")));
   const link=make("a","Actions実行記録 #"+x.id);link.href=GH+"/actions/runs/"+x.id;link.rel="noopener noreferrer";card.append(link);preservationArea.append(card);
  }
  preservationStatus.textContent=rows.length+" 件 / "+new Date().toLocaleString("ja-JP")+"（公開実行情報）";return true;
 }catch(e){preservationStatus.textContent="更新失敗: "+e.message+"。前回取得分を保持。";return false;}
}
function renderRecent(){
 if(!snapshot)return;
 const rows=selectRecentArtifacts(snapshot,categorySelect.value);
 area.replaceChildren();
  for(const x of rows){
   const card=make("article","");card.className="tile";card.dataset.artifactId=String(x.id);
   card.style.overflowWrap="anywhere";card.append(make("h3",x.category),make("p",x.name),make("p","制作日時 "+new Date(x.created).toLocaleString("ja-JP")+" / HEAD "+x.head.slice(0,12)),make("p","未公開候補・内容／QA／採用未判定（公開メタデータ）"));
   if(Number.isFinite(Date.parse(x.expires))){
    const remaining=Date.parse(x.expires)-Date.now();
    card.append(make("p","元Artifact期限 "+new Date(x.expires).toLocaleString("ja-JP")+(remaining<=48*3600000?" / 48時間以内または失効（保全状況は不明）":"")));
   }
   const link=make("a","GitHubで原Artifactを取得");link.href=GH+"/actions/runs/"+x.run+"/artifacts/"+x.id;link.rel="noopener noreferrer";card.append(link);
   const run=make("a","生成元Actions・実行結果");run.href=GH+"/actions/runs/"+x.run;run.rel="noopener noreferrer";card.append(run);
   if(x.bytes<=128*1024*1024){
    const b=make("button","取得したZIPを端末内で見る");b.type="button";
    b.addEventListener("click",()=>{
     const panel=document.getElementById("local-title"),file=document.getElementById("artifact-zip"),filter=document.getElementById("zip-image-filter"),digest=document.getElementById("artifact-digest");
     panel.open=true;filter.value=x.filter;digest.value=x.digest.replace(/^sha256:/,"");
     document.getElementById("zip-status").textContent="対象 "+x.name+" のZIPを選択し、必要に応じSHA照合後、ZIP内画像を表示してください。";
     file.scrollIntoView({block:"center"});file.focus({preventScroll:true});
    });card.append(b);
   }else card.append(make("p","128 MiB超：GitHubで取得後、端末上で展開してください。"));
   area.append(card);
  }
 status.textContent=rows.length+" 件（直近100 Artifact中、既知の制作元・期限内のみ、選択領域ごと最大30件）／ "+lastSuccess+(rows.length?"":"。対象未検出の場合は担当PRを確認。")+(lastError?" / 更新失敗: "+lastError+"。前回取得分を保持。":"");
}
categorySelect.addEventListener("change",renderRecent);
async function update(){
 if(busy||document.hidden)return;
 busy=true;if(timer!==null)clearTimeout(timer);timer=null;
 const g=++generation;refresh.disabled=true;status.textContent="最新Artifactの公開メタデータを取得中";
 const preservation=updatePreservation();let success=false;
 try{
  const data=await publicJson("/actions/artifacts?per_page=100");
  if(g!==generation)return;
  selectRecentArtifacts(data); // Validate before replacing the prior snapshot.
  snapshot=data;lastSuccess=new Date().toLocaleString("ja-JP");lastError="";
  renderRecent();success=true;
 }catch(e){if(g===generation){lastError=e.message;status.textContent="最新一覧取得失敗: "+lastError+"。前回取得分を保持。担当PRから確認できます。";}}
 finally{
  const preservationSuccess=await preservation;
  if(g===generation){refresh.disabled=false;busy=false;nextDue=Date.now()+refreshDelay(success&&preservationSuccess);schedule();}
 }
}
document.addEventListener("visibilitychange",()=>{if(document.hidden){if(timer!==null)clearTimeout(timer);timer=null;}else schedule();});
refresh.addEventListener("click",update);update();
})();
