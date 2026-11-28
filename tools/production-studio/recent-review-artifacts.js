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
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?(?:hero-tree|tree|trees)(?:-|$)/,"世界・樹木",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?forest(?:-|$)/,"世界・森林",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?sanctuary(?:-|$)/,"世界・聖域",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?ruins?(?:-|$)/,"世界・遺跡",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?(?:ireland-)?(?:river|waterway|riverbank)(?:-|$)/,"世界・河川／水辺",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?(?:ireland-)?(?:dem|terrain|terrace)(?:-|$)/,"世界・地形",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-(?:v\d+-)?(?:fern|plant|grass|vegetation|flower)(?:-|$)/,"世界・植物／草花",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^two-[a-z0-9][a-z0-9-]{0,159}$/,"世界・新規制作証跡（未分類）",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^(?:ireland|two-shared|lind|world|area)/i,"地図・エリア設計",""],
 ["feature/studio-sync-coverage-20261125",/^studio-sync-preview$/,"内部ギャラリー履歴","published/"],
];
const REPO_ID=1408120919;
const FALLBACK="その他・未分類";
function inferCategory(branch,name){
 const key=(branch+" "+name).toLowerCase();
 if(/morwen|vroid/.test(key)){
  if(/wardrobe|textile|garment|costume|cloth/.test(key))return "モルウェン・衣装";
  if(/hair/.test(key))return "モルウェン・顔／髪";
  if(/vrm|blender|transfer/.test(key))return "モルウェン・Blender移行／造形";
  return "モルウェン・造形";
 }
 if(/cliff|windwaiting/.test(key))return "風待ちの崖";
 if(/ecology|vegetation|lind-eco/.test(key))return "リルド村・植生";
 if(/home|aidan/.test(key))return "リルド村・エイダン家";
 if(/building|architecture|lind-village|village|turf/.test(key))return "リルド村・建築";
 if(/forest/.test(key))return "世界・森林";
 if(/tree/.test(key))return "世界・樹木";
 if(/river|waterway|riverbank/.test(key))return "世界・河川／水辺";
 if(/sanctuary/.test(key))return "世界・聖域";
 if(/ruin/.test(key))return "世界・遺跡";
 if(/terrain|dem|terrace/.test(key))return "世界・地形";
 if(/plant|grass|flower|fern/.test(key))return "世界・植物／草花";
 if(/blueprint|ireland-world|region|area-map/.test(key))return "地図・エリア設計";
 if(/(?:^|[\s/_.-])(?:audio|music|bgm|sound)(?:$|[\s/_.-])/.test(key))return "音楽・音響";
 if(/studio|preservation|engine|qualification|infra|recovery|handoff/.test(key))return "制作基盤・QA";
 if(/game|runtime|battle|ui-ux|webgl/.test(key))return "ゲーム・UI／実装";
 return FALLBACK;
}
const CATEGORIES=[...new Set([...RULES.map(r=>r[2]),"モルウェン・Blender移行／造形","制作基盤・QA","ゲーム・UI／実装","音楽・音響",FALLBACK])];
function safeLabel(s){return typeof s==="string"&&s.length>0&&s.length<=180&&!/[\x00-\x1f\x7f]/.test(s);}
function selectLiveRuns(data){
 if(!Array.isArray(data?.workflow_runs))throw Error("Actions一覧形式不正");
 const seen=new Set(),rows=[];
 for(const x of data.workflow_runs.slice(0,100)){
  if(!isId(x?.id)||seen.has(x.id)||x.repository?.full_name!==REPO||x.head_repository?.full_name!==REPO||
     !safeLabel(x.head_branch)||!safeLabel(x.name)||!/^\.github\/workflows\/[A-Za-z0-9_.-]+\.ya?ml$/.test(x.path||"")||
     !/^[a-f0-9]{40}$/.test(x.head_sha||"")||!Number.isFinite(Date.parse(x.updated_at))||
     !["queued","waiting","pending","requested","in_progress","completed"].includes(x.status))continue;
  if(x.conclusion==="skipped"||/^(pages build and deployment|morwen scoped comment launch)$/i.test(x.name))continue;
  const category=inferCategory(x.head_branch,x.name+" "+x.path);
  seen.add(x.id);
  rows.push({id:x.id,name:x.name,head:x.head_sha,category,status:x.status,conclusion:typeof x.conclusion==="string"?x.conclusion:null,updated:x.updated_at});
 }
 return rows.sort((a,b)=>Number(a.status==="completed")-Number(b.status==="completed")||Date.parse(b.updated)-Date.parse(a.updated)||b.id-a.id);
}
function swipeDirection(dx,dy){return Math.abs(dx)>=56&&Math.abs(dx)>Math.abs(dy)*1.5?(dx<0?1:-1):0;}
const SOURCE_LINKS=[
 ["リルド村・植生","/pull/357"],
 ["モルウェン・材質研究","/pull/540"],
 ["モルウェン・顔／髪","/pull/427"],
 ["風待ちの崖","/pull/421"],
 ["リルド村・エイダン家","/pull/364"],
 ["世界・植物／草花","/pull/482"],
 ["世界・河川／水辺","/pull/482"],
 ["世界・地形","/pull/482"],
 ["世界・樹木","/pull/482"],
 ["世界・森林","/pull/482"],
 ["世界・遺跡","/pull/482"],
 ["世界・聖域","/pull/482"],
 ["世界・新規制作証跡（未分類）","/pull/482"],
 ["地図・エリア設計","/pull/482"],
 ["音楽・音響","/pull/631"]
];
const isId=n=>Number.isSafeInteger(n)&&n>0;
const REFRESH_MS=5*60*1000, RETRY_MS=15*60*1000, PRESERVATION_MS=30*60*1000;
const REPORT_SOURCES=new Map([[427,"モルウェン・造形"],[540,"モルウェン・衣装"],[474,"モルウェン・ヘア技術"],[421,"風待ちの崖"],[364,"リルド村・建築"],[357,"リルド村・植生"],[482,"世界・エリア制作"],[608,"3D描画技術"]]);
// Public producer reports are evidence links, never inferred artifact/QA approval.
function selectProductionReports(data){
 if(!Array.isArray(data))throw Error("制作報告一覧形式不正");
 const seen=new Set(),rows=[];
 for(const c of data.slice(0,100)){
  const prefix=API+"/issues/";
  if(!c||!isId(c.id)||seen.has(c.id)||typeof c.issue_url!=="string"||!c.issue_url.startsWith(prefix))continue;
  const suffix=c.issue_url.slice(prefix.length);
  if(!/^[1-9]\d*$/.test(suffix))continue;
  const pr=Number(suffix);
  if(!REPORT_SOURCES.has(pr)||c.user?.login!=="celticmusic-nagoya"||c.html_url!==GH+"/pull/"+pr+"#issuecomment-"+c.id||!Number.isFinite(Date.parse(c.updated_at)))continue;
  // Only already-public report text; never interpret HTML/markdown or expose attachments.
  if(typeof c.body!=="string"||!c.body.trim())continue;
  const excerpt=c.body.replace(/[\x00-\x1f\x7f]/g," ").replace(/\s+/g," ").trim().slice(0,220);
  seen.add(c.id);rows.push({id:c.id,pr,category:REPORT_SOURCES.get(pr),updated:c.updated_at,excerpt});
 }
 return rows.sort((a,b)=>Date.parse(b.updated)-Date.parse(a.updated)||b.id-a.id);
}
function mergeProductionReports(previous,current){
 const byId=new Map(previous.map(x=>[x.id,x]));
 for(const x of current)byId.set(x.id,x);
 const counts=new Map(),out=[];
 for(const x of [...byId.values()].sort((a,b)=>Date.parse(b.updated)-Date.parse(a.updated)||b.id-a.id)){
  if((counts.get(x.pr)||0)>=3)continue;counts.set(x.pr,(counts.get(x.pr)||0)+1);out.push(x);
 }
 return out;
}
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
function selectRecentArtifacts(data,category="",limit=30){
 if(!Array.isArray(data?.artifacts))throw Error("Artifact一覧形式不正");
 const seen=new Set(), rows=[];
 for(const a of data.artifacts.slice(0,100)){
  const w=a?.workflow_run;
  if(!isId(a?.id)||seen.has(a.id)||!isId(w?.id)||!safeLabel(a.name)||
     !safeLabel(w.head_branch)||!/^[a-f0-9]{40}$/.test(w.head_sha||"")||
     w.repository_id!==REPO_ID||w.repository_id!==w.head_repository_id||
     a.expired!==false||!isId(a.size_in_bytes)||!Number.isFinite(Date.parse(a.created_at)))continue;
  if(w.head_branch==="docs/ireland-world-source-grounded-plan-20261123"&&a.name.startsWith("two-")&&!/^two-[a-z0-9][a-z0-9-]{0,159}$/i.test(a.name))continue;
 const rule=RULES.find(([branch,pattern])=>w.head_branch===branch&&pattern.test(a.name));
  // Fallback is metadata only, never image or native-file publication approval.
  const fallback=!rule&&w.repository_id===REPO_ID&&safeLabel(a.name)&&safeLabel(w.head_branch)&&/^[A-Za-z0-9][A-Za-z0-9_. -]{0,179}$/.test(a.name);
  if(!rule&&!fallback)continue;
  const classified=rule?rule[2]:inferCategory(w.head_branch,a.name);
  if(category&&classified!==category)continue;
  seen.add(a.id);
  rows.push({id:a.id,run:w.id,name:a.name,head:w.head_sha,branch:w.head_branch,category:classified,filter:rule?rule[3]:"",metadataOnly:!rule,
    created:a.created_at,expires:a.expires_at||"",bytes:a.size_in_bytes,
    digest:/^sha256:[a-f0-9]{64}$/.test(a.digest||"")?a.digest:""});
 }
 return rows.sort((a,b)=>Date.parse(b.created)-Date.parse(a.created)||b.id-a.id).slice(0,limit);
}
// Metadata only; never proof of backup or restoration.
const HOUR=3600000;
function expiryState(row,now){
 const end=typeof row.expires==="string"?Date.parse(row.expires):NaN;
 if(!Number.isFinite(end)||!Number.isFinite(now))return "unknown";
 if(end<=now)return "elapsed";
 if(end-now<=48*HOUR)return "urgent";
 if(end-now<=168*HOUR)return "soon";
 return "later";
}
function expirySummary(rows,now){
 const out={elapsed:0,urgent:0,soon:0,later:0,unknown:0};
 for(const row of rows)out[expiryState(row,now)]++;
 return out;
}
function orderExpiry(rows,now){
 const priority={urgent:0,soon:1,unknown:2,elapsed:3,later:4};
 return rows.filter(x=>expiryState(x,now)!=="later").slice().sort((a,b)=>{
  const av=expiryState(a,now),bv=expiryState(b,now);
  return priority[av]-priority[bv]||(Number.isFinite(Date.parse(a.expires))&&Number.isFinite(Date.parse(b.expires))?Date.parse(a.expires)-Date.parse(b.expires):0)||b.id-a.id;
 });
}
function recoveryLocator(row,observedAt){
 if(!isId(row?.id)||!isId(row.run)||!safeLabel(row.name)||!safeLabel(row.branch)||!/^[a-f0-9]{40}$/.test(row.head||"")||!isId(row.bytes)||!Number.isFinite(Date.parse(observedAt)))throw Error("復元情報不正");
 return {schema:"two.studio.artifact-locator.v1",repository:REPO,artifact_id:row.id,run_id:row.run,head_sha:row.head,head_branch:row.branch,name:row.name,
  archive_bytes:row.bytes,archive_digest:/^sha256:[a-f0-9]{64}$/.test(row.digest||"")?row.digest:null,
  created_at:Number.isFinite(Date.parse(row.created))?row.created:null,
  expires_at:Number.isFinite(Date.parse(row.expires))?row.expires:null,metadata_observed_at:observedAt,
  original_artifact_url:GH+"/actions/runs/"+row.run+"/artifacts/"+row.id,
  preservation_status:"UNVERIFIED",byte_verification:"NOT_RUN",adoption:"UNDETERMINED",
  note:"Public metadata locator only. Not a backup, approval, source availability guarantee or evidence of restoration. Verify exact bytes with authorized owner and preservation ledger."};
}
if(typeof module!=="undefined")module.exports={expiryState,expirySummary,orderExpiry,recoveryLocator,selectRecentArtifacts,selectPreservationRuns,refreshDelay,selectLiveRuns,swipeDirection,inferCategory,selectProductionReports,mergeProductionReports};
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
const cadence=make("p","公開Actions・Artifact・担当PR制作報告は表示中5分ごとに照会（手動更新可）。保全実行情報は30分ごと、承認済み公開画像は別一覧で1分ごと。通信失敗時は15分間隔に抑制。未保存・非公開の作業ファイルは取得できません。");
cadence.className="note";
const categoryLabel=make("label","制作領域で絞り込み");
const categorySelect=make("select","");categorySelect.id="recent-review-category";categoryLabel.htmlFor=categorySelect.id;
for(const name of ["",...CATEGORIES]){const option=make("option",name||"すべての制作領域");option.value=name;categorySelect.append(option);}
categorySelect.value="";
const sources=make("p","過去の成果物・一覧未検出時： ");sources.className="note";
for(const [name,path] of SOURCE_LINKS){const link=make("a",name+" / 担当PR");link.href=GH+path;link.rel="noopener noreferrer";sources.append(link,make("span","　"));}
const categoryGrid=make("div","");categoryGrid.id="recent-category-grid";categoryGrid.className="recent-category-grid";categoryGrid.setAttribute("aria-label","制作領域別の成果物件数");
const searchLabel=make("label","制作成果物を検索");const search=make("input","");search.type="search";search.id="recent-review-search";search.placeholder="名称・バージョン・HEAD・Artifact ID";searchLabel.htmlFor=search.id;
const expiryBox=make("div","");expiryBox.className="tile";
const expiryHeading=make("h3","期限・復元情報");
const expiryStatus=make("p","未取得");expiryStatus.id="artifact-expiry-summary";expiryStatus.setAttribute("role","status");
const expiryToggle=make("button","期限確認を優先");expiryToggle.type="button";expiryToggle.id="artifact-expiry-toggle";expiryToggle.setAttribute("aria-pressed","false");
expiryBox.append(expiryHeading,make("p","最新取得範囲の期限情報。原本保全の有無は未確認。必要な成果物だけ担当PR・既存非公開保全経路で確認してください。"),expiryStatus,expiryToggle);
refresh.after(cadence,categoryLabel,categorySelect,sources,categoryGrid,searchLabel,search,expiryBox);
const reportsHeading=make("h3","新着制作報告（画像未登録・チャット内制作を含む）");
reportsHeading.id="recent-production-reports-title";
const reportsStatus=make("p","未取得");reportsStatus.setAttribute("role","status");
const reportsArea=make("section","");reportsArea.id="recent-production-reports";reportsArea.className="grid";reportsArea.setAttribute("aria-labelledby",reportsHeading.id);
const reportHint=make("p","担当PRの公開報告を参照。報告と実ファイルの保存・画像公開・独立QAは別です。直近100コメントの取得範囲に限定。");
reportHint.className="note";
const liveHeading=make("h3","制作中・最近の実行");
const liveStatus=make("p","未取得");liveStatus.setAttribute("role","status");
const liveArea=make("section","");liveArea.id="recent-live-runs";liveArea.className="grid";
const artifactHeading=make("h3","保存済みArtifact");
const swipeHint=make("p","カテゴリを左右にスワイプ、または前へ／次へ。画像拡大中も左右スワイプで切替（等倍時のみ）。");swipeHint.className="note";
const swipeBar=make("div","");swipeBar.className="recent-swipe-bar";
const back=make("button","← 前のカテゴリ"),forward=make("button","次のカテゴリ →");
back.type=forward.type="button";swipeBar.append(back,forward);
const more=make("button","さらに表示");more.type="button";more.hidden=true;
if(typeof area.before==="function")area.before(reportsHeading,reportHint,reportsStatus,reportsArea,swipeHint,swipeBar,liveHeading,liveStatus,liveArea,artifactHeading);
if(typeof area.after==="function")area.after(more);
let generation=0,timer=null,nextDue=0,busy=false,snapshot=null,lastSuccess="",lastObservedAt="",lastError="",runSnapshot=[],runError="",runStamp="",visibleLimit=30,expiryFirst=false;
expiryToggle.addEventListener("click",()=>{expiryFirst=!expiryFirst;expiryToggle.setAttribute("aria-pressed",String(expiryFirst));expiryToggle.textContent=expiryFirst?"すべての期限を表示":"期限確認を優先";visibleLimit=30;renderRecent();});
let reportRows=[],reportStamp="",reportError="",preservationDue=0;
let visibleCategories=[""];
function renderReports(){
 reportsArea.replaceChildren();
 for(const x of reportRows){
  const card=make("article","");card.className="tile";card.dataset.reportId=String(x.id);
  card.append(make("h4",x.category),make("p","報告更新 "+new Date(x.updated).toLocaleString("ja-JP")+" / PR #"+x.pr),make("p",x.excerpt),make("p","公開PR報告・画像／成果物実体／QA未確認"));
  const a=make("a","制作報告の全文・証跡");a.href=GH+"/pull/"+x.pr+"#issuecomment-"+x.id;a.rel="noopener noreferrer";card.append(a);reportsArea.append(card);
 }
 reportsStatus.textContent=reportRows.length+" 件（各PR最大3件・取得済み報告） / "+(reportStamp||"未取得")+(reportError?" / 更新失敗: "+reportError+"。前回分を保持。":" / 全履歴・実ファイルは未確認");
}
async function updateReports(){
 try{
  const rows=selectProductionReports(await publicJson("/issues/comments?sort=updated&direction=desc&per_page=100"));
  reportRows=mergeProductionReports(reportRows,rows);reportStamp=new Date().toLocaleString("ja-JP");reportError="";return true;
 }catch(e){reportError=e.message;return false;}
 finally{renderReports();}
}
function chooseCategory(name){categorySelect.value=name;visibleLimit=30;renderRecent();const current=typeof categoryGrid.querySelector==="function"?categoryGrid.querySelector('button[aria-pressed="true"]'):null;if(current&&categoryGrid.scrollWidth>categoryGrid.clientWidth)categoryGrid.scrollLeft+=current.getBoundingClientRect().left-categoryGrid.getBoundingClientRect().left;}
function shiftCategory(delta){
 const i=visibleCategories.indexOf(categorySelect.value);const next=i+delta;
 if(next>=0&&next<visibleCategories.length)chooseCategory(visibleCategories[next]);
}
back.addEventListener("click",()=>shiftCategory(-1));forward.addEventListener("click",()=>shiftCategory(1));
more.addEventListener("click",()=>{visibleLimit+=30;renderRecent();});
// Passive touch listeners leave vertical scrolling and pinch zoom alone.
let touch=null;
document.addEventListener("touchstart",e=>{
 if(e.touches.length!==1){touch=null;return;}
 const target=e.target;
 if(!target?.closest||target.closest("input,select,textarea,a,button,canvas,#model-view")){touch=null;return;}
 const lightbox=target.closest(".gallery-lightbox");
 const viewport=target.closest('[aria-label="画像拡大表示"]');
 const categories=target.closest("#recent-category-grid,#recent-live-runs,#recent-review-artifacts");
 if(lightbox&&viewport&&viewport.scrollWidth<=viewport.clientWidth+2&&viewport.scrollHeight<=viewport.clientHeight+2){
  touch={x:e.touches[0].clientX,y:e.touches[0].clientY,dialog:lightbox};
 }else if(categories&&!lightbox)touch={x:e.touches[0].clientX,y:e.touches[0].clientY};
 else touch=null;
},{passive:true});
document.addEventListener("touchcancel",()=>{touch=null;},{passive:true});
document.addEventListener("touchend",e=>{
 const start=touch;touch=null;if(!start||e.touches.length||e.changedTouches.length!==1)return;
 const p=e.changedTouches[0],delta=swipeDirection(p.clientX-start.x,p.clientY-start.y);if(!delta)return;
 if(start.dialog){const btn=[...start.dialog.querySelectorAll("button")].find(b=>b.textContent===(delta>0?"次へ →":"← 前へ"));if(btn&&!btn.disabled)btn.click();}
 else shiftCategory(delta);
},{passive:true});
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
 if(!snapshot&&!runSnapshot.length){liveStatus.textContent=runError?"取得失敗: "+runError:"未取得";return;}
 const all=snapshot?selectRecentArtifacts(snapshot,"",100):[];
 const now=Date.now(),risk=expirySummary(all,now);
 expiryStatus.textContent=snapshot?("取得 "+all.length+"件｜48時間以内 "+risk.urgent+"件 / 2〜7日以内 "+risk.soon+"件 / 期限経過 "+risk.elapsed+"件 / 期限不明 "+risk.unknown+"件"+(lastError?"｜取得失敗・前回記録":"")+"｜保全未確認"):"未取得";
 const counts=new Map();for(const x of all)counts.set(x.category,(counts.get(x.category)||0)+1);
 const runCounts=new Map();for(const x of runSnapshot)runCounts.set(x.category,(runCounts.get(x.category)||0)+1);
 visibleCategories=["",...CATEGORIES.filter(name=>counts.has(name)||runCounts.has(name)||name.startsWith("世界・")||name===categorySelect.value)];
 back.disabled=visibleCategories.indexOf(categorySelect.value)<=0;forward.disabled=visibleCategories.indexOf(categorySelect.value)>=visibleCategories.length-1;
 categoryGrid.replaceChildren();
 for(const name of visibleCategories){
  const button=make("button",(name||"すべて")+"（"+(name?counts.get(name)||0:all.length)+"件 / 実行 "+(name?runCounts.get(name)||0:runSnapshot.length)+"）");button.type="button";button.dataset.category=name;button.setAttribute("aria-pressed",String(categorySelect.value===name));
  button.addEventListener("click",()=>chooseCategory(name));categoryGrid.append(button);
 }
 const query=String(search.value||"").trim().toLowerCase();
 const filtered=all.filter(x=>(!categorySelect.value||x.category===categorySelect.value)&&(!query||[x.name,x.category,x.head,x.id,x.run].join(" ").toLowerCase().includes(query)));
 const eligible=expiryFirst?orderExpiry(filtered,now):filtered;
 const rows=eligible.slice(0,visibleLimit);more.hidden=rows.length>=eligible.length;
 const runRows=runSnapshot.filter(x=>(!categorySelect.value||x.category===categorySelect.value)&&(!query||[x.name,x.category,x.head,x.id].join(" ").toLowerCase().includes(query)));
 liveArea.replaceChildren();
 for(const x of runRows.slice(0,visibleLimit)){
  const card=make("article","");card.className="tile live-run-card";card.dataset.runId=String(x.id);
  const state=x.status==="completed"?(x.conclusion||"結果未確定"):({"in_progress":"制作中","queued":"待機中","waiting":"承認・実行待ち","pending":"待機中","requested":"起動要求済み"}[x.status]||x.status);
  const label=make("span",state);label.className="live-run-state";label.dataset.state=x.status;
  card.append(label,make("h4",x.category),make("p",x.name),make("p","更新 "+new Date(x.updated).toLocaleString("ja-JP")+" / HEAD "+x.head.slice(0,12)),make("p","公開実行情報のみ・成果物とQAは未確認"));
  const a=make("a","Actions・進行状況 #"+x.id);a.href=GH+"/actions/runs/"+x.id;a.rel="noopener noreferrer";card.append(a);liveArea.append(card);
 }
 more.hidden=rows.length>=eligible.length&&runRows.length<=visibleLimit;
 liveStatus.textContent=runRows.length+" 実行（表示 "+Math.min(runRows.length,visibleLimit)+"） / "+(runStamp||"未取得")+(runError?" / 取得失敗・前回分: "+runError:"");
 area.replaceChildren();
  for(const x of rows){
   const card=make("article","");card.className="tile";card.dataset.artifactId=String(x.id);
   card.style.overflowWrap="anywhere";card.append(make("h3",x.category),make("p",x.name),make("p","制作日時 "+new Date(x.created).toLocaleString("ja-JP")+" / HEAD "+x.head.slice(0,12)),make("p","未公開候補・内容／QA／採用未判定（公開メタデータ）"));
   const expiry=expiryState(x,now),expiryLabel={urgent:"48時間以内",soon:"2〜7日以内",later:"7日超",elapsed:"期限経過・取得可否未確認",unknown:"期限不明"};
   card.dataset.expiry=expiry;
   card.append(make("p","元Artifact期限 "+(expiry==="unknown"?"不明":new Date(x.expires).toLocaleString("ja-JP"))+" / "+expiryLabel[expiry]+"（保全未確認）"));
   if(expiry==="urgent"||expiry==="soon")card.append(make("p","必要な原本・成果物は担当PRで保全状況を確認してください。"));
   const locator=make("button","復元情報JSONを保存");locator.type="button";
   locator.addEventListener("click",()=>{
    const receipt=recoveryLocator(x,lastObservedAt);
    const url=URL.createObjectURL(new Blob([JSON.stringify(receipt,null,2)+"\n"],{type:"application/json"}));
    const a=make("a","");a.href=url;a.download="two-artifact-"+x.id+"-locator.json";a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
   });card.append(locator);
   const link=make("a","GitHubで原Artifactを取得");link.href=GH+"/actions/runs/"+x.run+"/artifacts/"+x.id;link.rel="noopener noreferrer";card.append(link);
   const run=make("a","生成元Actions・実行結果");run.href=GH+"/actions/runs/"+x.run;run.rel="noopener noreferrer";card.append(run);
   if(!x.metadataOnly&&x.bytes<=128*1024*1024){
    const b=make("button","取得したZIPを端末内で見る");b.type="button";
    b.addEventListener("click",()=>{
     const panel=document.getElementById("local-title"),file=document.getElementById("artifact-zip"),filter=document.getElementById("zip-image-filter"),digest=document.getElementById("artifact-digest");
     panel.open=true;filter.value=x.filter;digest.value=x.digest.replace(/^sha256:/,"");
     document.getElementById("zip-status").textContent="対象 "+x.name+" のZIPを選択し、必要に応じSHA照合後、ZIP内画像を表示してください。";
     file.scrollIntoView({block:"center"});file.focus({preventScroll:true});
    });card.append(b);
   }else card.append(make("p",x.metadataOnly?"新規・未分類候補：公開メタデータのみ。内容と権利を確認後に画像登録。":"128 MiB超：GitHubで取得後、端末上で展開してください。"));
   area.append(card);
  }
 status.textContent=rows.length+" 件（直近100 Artifact中、API未失効フラグ・同一制作元、表示 "+rows.length+" / "+eligible.length+"）／ "+lastSuccess+(rows.length?"":"。対象未検出の場合は担当PRを確認。")+(lastError?" / 更新失敗: "+lastError+"。前回取得分を保持。":"");
}
categorySelect.addEventListener("change",()=>{visibleLimit=30;renderRecent();});
search.addEventListener("input",()=>{visibleLimit=30;renderRecent();});
async function updateRuns(){try{runSnapshot=selectLiveRuns(await publicJson("/actions/runs?per_page=100"));runStamp=new Date().toLocaleString("ja-JP");runError="";return true;}catch(e){runError=e.message;return false;}}
async function update(){
 if(busy||document.hidden)return;
 busy=true;if(timer!==null)clearTimeout(timer);timer=null;
 const g=++generation;refresh.disabled=true;status.textContent="最新Artifactの公開メタデータを取得中";
 const preservation=Date.now()>=preservationDue?updatePreservation().then(ok=>{preservationDue=Date.now()+(ok?PRESERVATION_MS:RETRY_MS);return ok}):Promise.resolve(true);
 const runs=updateRuns(),reports=updateReports();let success=false;
 try{
  const data=await publicJson("/actions/artifacts?per_page=100");
  if(g!==generation)return;
  selectRecentArtifacts(data); // Validate before replacing the prior snapshot.
  snapshot=data;lastObservedAt=new Date().toISOString();lastSuccess=new Date(lastObservedAt).toLocaleString("ja-JP");lastError="";
  success=true;
 }catch(e){if(g===generation){lastError=e.message;status.textContent="最新一覧取得失敗: "+lastError+"。前回取得分を保持。担当PRから確認できます。";}}
 finally{
  const [preservationSuccess,runsSuccess,reportsSuccess]=await Promise.all([preservation,runs,reports]);
  if(g===generation){renderRecent();refresh.disabled=false;busy=false;nextDue=Date.now()+refreshDelay(success&&preservationSuccess&&runsSuccess&&reportsSuccess);schedule();}
 }
}
document.addEventListener("visibilitychange",()=>{if(document.hidden){if(timer!==null)clearTimeout(timer);timer=null;}else schedule();});
refresh.addEventListener("click",update);update();
})();
