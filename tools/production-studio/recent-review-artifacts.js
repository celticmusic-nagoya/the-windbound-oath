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
 ["infra/native-env-qualification-20261123",/^two-hairharpy-volume-/,"モルウェン・ヘア技術",""],
 ["docs/ireland-world-source-grounded-plan-20261123",/^(?:ireland|two-shared|lind|world|area)/i,"地図・エリア設計",""],
 ["feature/studio-sync-coverage-20261125",/^studio-sync-preview$/,"内部ギャラリー履歴","published/"],
];
const isId=n=>Number.isSafeInteger(n)&&n>0;
function selectRecentArtifacts(data){
 if(!Array.isArray(data?.artifacts))throw Error("Artifact一覧形式不正");
 const seen=new Set(), rows=[];
 for(const a of data.artifacts.slice(0,100)){
  const w=a?.workflow_run;
  if(!isId(a?.id)||seen.has(a.id)||!isId(w?.id)||typeof a.name!=="string"||
     typeof w.head_branch!=="string"||!/^[a-f0-9]{40}$/.test(w.head_sha||"")||
     !isId(w.repository_id)||w.repository_id!==w.head_repository_id||
     a.expired!==false||!isId(a.size_in_bytes)||!Number.isFinite(Date.parse(a.created_at)))continue;
  const rule=RULES.find(([branch,pattern])=>w.head_branch===branch&&pattern.test(a.name));
  if(!rule)continue;
  seen.add(a.id);
  rows.push({id:a.id,run:w.id,name:a.name,head:w.head_sha,category:rule[2],filter:rule[3],
    created:a.created_at,expires:a.expires_at||"",bytes:a.size_in_bytes,
    digest:/^sha256:[a-f0-9]{64}$/.test(a.digest||"")?a.digest:""});
 }
 return rows.sort((a,b)=>Date.parse(b.created)-Date.parse(a.created)||b.id-a.id).slice(0,30);
}
if(typeof module!=="undefined")module.exports={selectRecentArtifacts};
if(typeof document==="undefined")return;
const area=document.getElementById("recent-review-artifacts"),status=document.getElementById("recent-review-status"),refresh=document.getElementById("refresh-recent-review");
if(!area||!status||!refresh)return;
const make=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;};
let generation=0;
async function update(){
 const g=++generation;refresh.disabled=true;status.textContent="最新Artifactの公開メタデータを取得中";
 try{
  const res=await fetch(API+"/actions/artifacts?per_page=100",{credentials:"omit",cache:"no-store",signal:AbortSignal.timeout(10000),headers:{Accept:"application/vnd.github+json"}});
  if(!res.ok)throw Error("HTTP "+res.status);
  const rows=selectRecentArtifacts(await res.json());
  if(g!==generation)return;
  area.replaceChildren();
  for(const x of rows){
   const card=make("article","");card.className="tile";card.dataset.artifactId=String(x.id);
   card.style.overflowWrap="anywhere";card.append(make("h3",x.category),make("p",x.name),make("p","制作日時 "+new Date(x.created).toLocaleString("ja-JP")+" / HEAD "+x.head.slice(0,12)),make("p","未公開候補・内容／QA／採用未判定（公開メタデータ）"));
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
  status.textContent=rows.length+" 件（直近100 Artifact中、既知の制作元・期限内のみ、最大30件）／ "+new Date().toLocaleString("ja-JP")+(rows.length?"":"。対象未検出の場合は下記の制作元を確認。");
 }catch(e){if(g===generation)status.textContent="最新一覧取得失敗: "+e.message+"。下記の制作元Actionsから確認できます。";}
 finally{if(g===generation)refresh.disabled=false;}
}
refresh.addEventListener("click",update);update();
})();
