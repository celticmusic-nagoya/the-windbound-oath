"use strict";
let publishedGalleryGeneration=0,publishedGalleryActive=0,publishedGalleryTimer=null,publishedGalleryDue=0;
let publishedGalleryKey=null,publishedGalleryView="home",publishedGalleryRemote=false;
let openGalleryCategory=null,pendingGalleryCategory=null;
const galleryProjectIds=new Set(["morwen","cliff","village"]);
document.addEventListener("studio:open-gallery-category",event=>{
 const id=event.detail;if(!galleryProjectIds.has(id))return;
 if(openGalleryCategory){openGalleryCategory(id);pendingGalleryCategory=publishedGalleryActive>0?id:null;}
 else{pendingGalleryCategory=id;document.getElementById("published-status").textContent="成果物一覧の取得待ち。必要に応じて成果物を更新してください。";}
});
const publishedGalleryLive=document.createElement("p");
publishedGalleryLive.id="published-live-status";publishedGalleryLive.className="note";publishedGalleryLive.setAttribute("role","status");
document.getElementById("published-status").after(publishedGalleryLive);
let publishedModelEpoch=0,publishedModelController=null;
function invalidatePublishedModel(){
 publishedModelEpoch++;
 publishedModelController?.abort();
 publishedModelController=null;
}
document.getElementById("model-file").addEventListener("change",invalidatePublishedModel);
window.addEventListener("pagehide",invalidatePublishedModel);
function schedulePublishedGallery(){
 if(publishedGalleryTimer!==null)clearTimeout(publishedGalleryTimer);
 publishedGalleryTimer=null;
 if(!document.hidden&&publishedGalleryActive===0)publishedGalleryTimer=setTimeout(()=>loadPublishedGallery(true),Math.max(0,publishedGalleryDue-Date.now()));
}
async function loadPublishedGallery(automatic=false){
 if(automatic&&(document.hidden||publishedGalleryActive>0))return;
 const generation=++publishedGalleryGeneration;
 publishedGalleryActive++;
 if(publishedGalleryTimer!==null)clearTimeout(publishedGalleryTimer);
 publishedGalleryTimer=null;
 const area=document.getElementById("published-gallery"), status=document.getElementById("published-status");
 let success=false;
 try{
 let base="./";
 let response;
 if(location.hostname==="celticmusic-nagoya.github.io"){
 const remote="https://raw.githubusercontent.com/celticmusic-nagoya/the-windbound-oath/studio-published/";
 try{response=await fetch(remote+"gallery-manifest.json",{cache:"no-store",credentials:"omit",signal:AbortSignal.timeout(8000)});if(response.ok)base=remote;}catch{}
 }
 if(!response?.ok&&publishedGalleryRemote)throw Error("公開同期元に接続できません");
 if(!response?.ok)response=await fetch("./gallery-manifest.json",{cache:"no-store",credentials:"omit",signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw Error("HTTP "+response.status);
 const manifest=await response.json();
 // A slower earlier request must never replace a newer gallery refresh.
 if(generation!==publishedGalleryGeneration)return;
 if(manifest.version!==1||!Array.isArray(manifest.entries)||manifest.entries.length>500)throw Error("一覧形式不正");
 const valid=[];
 for(const e of manifest.entries){
 if(!e||typeof e!=="object"||!/^[a-f0-9]{64}$/.test(e.sha256)||!new RegExp("^published/"+e.sha256+"\\.(png|jpg|jpeg|glb|vrm)$").test(e.path)||!Number.isSafeInteger(e.bytes)||e.bytes<1||e.bytes>64*1024*1024)continue;
 // Optional metadata must never crash grouping, filtering, or image comparison.
 if(typeof e.name!=="string"||typeof e.qa!=="string"||typeof e.adoption!=="string")continue;
 if(["stage","asset_id","source_path","category","subcategory","head","created_at"].some(k=>e[k]!=null&&typeof e[k]!=="string"))continue;
 valid.push(e);
 }
 const key=JSON.stringify([base,valid]);
 const stamp=new Date().toLocaleString("ja-JP");
 const source=base==="./"&&location.hostname==="celticmusic-nagoya.github.io"?"同梱版（最新同期未確認）":"公開一覧";
 const note=source+" / 最終照会 "+stamp+" / 表示中は1分ごとに自動照会";
 if(base!=="./")publishedGalleryRemote=true;
 success=true;
 if(automatic&&key===publishedGalleryKey){pendingGalleryCategory=null;publishedGalleryLive.textContent=note+" / 変更なし";return;}
 if(automatic&&publishedGalleryKey!==null&&publishedGalleryView!=="home"){pendingGalleryCategory=null;publishedGalleryLive.textContent=note+" / 新しい一覧あり。閲覧中の内容を保持しています。「成果物を更新」で反映。";return;}
 publishedGalleryKey=key;publishedGalleryLive.textContent=note+" / "+valid.length+" 件";
 const repoUrl="https://github.com/celticmusic-nagoya/the-windbound-oath";
 function provenance(e,parent){
  const add=(label,url,cls)=>{const a=document.createElement("a");a.textContent=label;a.href=url;a.className=cls;a.rel="noopener noreferrer";parent.append(a);};
  const note=document.createElement("p");note.className="gallery-source-expiry";
  const git=e.source_type==="git"&&/^[a-f0-9]{40}$/.test(e.head||"")&&typeof e.source_path==="string"&&/^assets\/candidates\/LIND-(HOME|BUILD)-01\/[\w./-]+\.png$/.test(e.source_path)&&e.source_path.split("/").every(part=>part&&part!=="."&&part!=="..");
  if(git){
   add("生成元 Git成果物",repoUrl+"/blob/"+e.head+"/"+e.source_path,"gallery-source-link");
   note.textContent="Git原本参照（Artifact期限なし・原本の存在は未再検証）";
  }else if(e.source_type!=="git"&&Number.isSafeInteger(e.run_id)&&e.run_id>0&&Number.isSafeInteger(e.artifact_id)&&e.artifact_id>0){
   const expiry=typeof e.expires_at==="string"?Date.parse(e.expires_at):NaN;
   const elapsed=Number.isFinite(expiry)&&expiry<=Date.now();
   note.textContent=Number.isFinite(expiry)?"原Artifact期限（記録）: "+e.expires_at+(elapsed?" / 経過済み（公開画像は保持）":" / 現在の可用性は未照会"):"原Artifact期限未記録（可用性未確認）";
   if(elapsed)add("生成元 Actions記録",repoUrl+"/actions/runs/"+e.run_id,"gallery-source-link");
   else add("生成元 Artifact（可用性未確認）",repoUrl+"/actions/runs/"+e.run_id+"/artifacts/"+e.artifact_id,"gallery-source-link");
  }else note.textContent="生成元の識別情報未確認（リンクなし）";
  parent.append(note);
  if(typeof e.review_ref==="string"&&/^https:\/\/github\.com\/celticmusic-nagoya\/the-windbound-oath\/(?:pull\/[1-9]\d*(?:#issuecomment-[1-9]\d*)?|blob\/[a-f0-9]{40}\/AGENTS\.md#director-approved-studio-work-in-progress-publication-2026-11-26)$/.test(e.review_ref))add("公開・レビュー根拠",e.review_ref,"gallery-review-link");
 }
 function renderEntry(e){
 const tile=document.createElement("article");tile.className="tile";
 const label=document.createElement("h3");label.textContent=e.name;tile.append(label);
 const meta=document.createElement("div");meta.className="gallery-meta";for(const [key,value] of [["QA",e.qa],["採用",e.adoption]]){const chip=document.createElement("span");chip.className="gallery-chip";chip.textContent=key+": "+value;meta.append(chip);}tile.append(meta);
 const preservation=document.createElement("p");preservation.className="gallery-preservation";preservation.textContent="原Artifact保全: "+(e.preservation_status==="PRESERVED_AND_READBACK_VERIFIED"?"manifest申告：再取得SHA検証済み（独立未検証）":e.preservation_status==="PRESERVATION_BLOCKED"?"権利確認待ち・未保全":"未検証（公開画像と原ZIPの保全は別）");tile.append(preservation);
 provenance(e,tile);
 if(/\.(png|jpe?g)$/.test(e.path)){const img=document.createElement("img");img.src=base+e.path;img.loading="lazy";img.alt=e.name;tile.prepend(img);}
 else {
 const button=document.createElement("button"), modelNote=document.createElement("p");
 button.textContent="3D表示";modelNote.setAttribute("role","status");
 button.onclick=async()=>{
  invalidatePublishedModel();
  const id=publishedModelEpoch,controller=new AbortController();
  publishedModelController=controller;
  button.disabled=true;modelNote.textContent="取得・SHA照合中";
  try{
   const res=await fetch(base+e.path,{credentials:"omit",signal:controller.signal});
   if(id!==publishedModelEpoch)return;
   if(!res.ok)throw Error("HTTP "+res.status);
   const reader=res.body.getReader();let size=0;const parts=[];
   try{while(true){const {done,value}=await reader.read();if(id!==publishedModelEpoch)return;if(done)break;size+=value.length;if(size>e.bytes)throw Error("容量不一致");parts.push(value);}}
   finally{try{await reader.cancel();}catch(err){if(id===publishedModelEpoch)throw err;}}
   const blob=new Blob(parts);
   const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",await blob.arrayBuffer())),x=>x.toString(16).padStart(2,"0")).join("");
   if(id!==publishedModelEpoch)return;
   if(size!==e.bytes||hash!==e.sha256)throw Error("SHA不一致");
   const input=document.getElementById("model-file"),dt=new DataTransfer();
   const panel=input.closest("details");if(panel)panel.open=true;
   dt.items.add(new File([blob],e.path.split("/").pop()));input.files=dt.files;
   publishedModelController=null;
   modelNote.textContent="SHA照合済み・表示処理へ引継ぎ";
   input.dispatchEvent(new Event("change"));
   document.getElementById("model-view").scrollIntoView({block:"center"});
  }catch(err){if(id===publishedModelEpoch)modelNote.textContent="モデル取得失敗: "+err.message;}
  finally{
   if(publishedModelController===controller)publishedModelController=null;
   if(id!==publishedModelEpoch&&modelNote.textContent==="取得・SHA照合中")modelNote.textContent="取得を中止しました";
   button.disabled=false;
  }
 };
 tile.append(button,modelNote);
 }
 return tile;
 }
 const categories=[["cliff","風待ちの崖"],["morwen","モルウェン"],["village","リルド村"],["world","世界・自然／遺構"],["blueprint","設計図"],["map","地図・配置図"],["other","その他"]];
 const subcategories={morwen:[["hair","ヘアアセット"],["body","身体・顔"],["wardrobe","衣装・装備"],["general","全体・その他"]],world:[["plant","植物・草花"],["tree","樹木"],["forest","森林"],["river","河川・水辺"],["terrain","地形"],["sanctuary","聖域"],["ruin","遺跡"],["general","世界・その他"]],village:[["aidan","エイダンの家"],["inn","宿屋"],["buildings","その他の建築"],["general","村全体・その他"]]};
 // Prefer explicit, publisher-provided subcategory. Legacy manifests may only carry a top-level category.
 const classify=e=>{
  const explicit=String(e.subcategory||"").toLowerCase();
  const raw=[e.name,e.stage,e.asset_id,e.source_path].filter(Boolean).join(" ").toLowerCase();
  const top=categories.some(([id])=>id===e.category)?e.category:e.run_id===44708204132?"cliff":"other";
  const hair=/hairharpy|hair[-_ ]asset|ヘアアセット/i.test(raw);
  const aidan=/aidan|エイダン/.test(raw);
  const inn=/(?:^|[^a-z])inn(?:$|[^a-z])|宿屋/.test(raw);
  const blueprint=/blueprint|design[-_ ]?sheet|設計図|四面図|寸法図|断面図/.test(raw);
  const map=/\bmap\b|site[-_ ]?plan|layout[-_ ]?plan|地図|配置図|平面図|俯瞰図/.test(raw);
  // Only explicit world categories or unambiguous world production names override legacy "other".
  const worldKind=/(?:^|[^a-z])(?:ruins?)(?:[^a-z]|$)|遺跡/.test(raw)?"ruin":/(?:^|[^a-z])sanctuary(?:[^a-z]|$)|聖域/.test(raw)?"sanctuary":/(?:^|[^a-z])forest(?:[^a-z]|$)|森林/.test(raw)?"forest":/(?:^|[^a-z])(?:hero[-_ ]tree|trees?)(?:[^a-z]|$)|樹木/.test(raw)?"tree":/(?:^|[^a-z])(?:river|waterway|waterside)(?:[^a-z]|$)|河川|水辺/.test(raw)?"river":/(?:^|[^a-z])(?:terrain|dem)(?:[^a-z]|$)|地形/.test(raw)?"terrain":/(?:^|[^a-z])(?:plant|grass|fern|flower|vegetation)(?:[^a-z]|$)|植物|草花/.test(raw)?"plant":"";
  const root=top==="other"?(blueprint?"blueprint":map?"map":hair?"morwen":aidan||inn?"village":worldKind?"world":"other"):top;
  const allowed=subcategories[root]||[];
  let sub=allowed.some(([id])=>id===explicit)?explicit:"";
  if(!sub&&root==="morwen")sub=hair?"hair":/face|body|顔|身体/.test(raw)?"body":/wardrobe|outfit|衣装|装備/.test(raw)?"wardrobe":"general";
  if(!sub&&root==="world")sub=worldKind||"general";
  if(!sub&&root==="village")sub=aidan?"aidan":inn?"inn":/building|建築/.test(raw)?"buildings":"general";
  return {root,sub};
 };
 const assigned=valid.map(e=>({entry:e,...classify(e)}));
 const groups=new Map(categories.map(([id])=>[id,assigned.filter(x=>x.root===id).map(x=>x.entry)]));
 const worldDesign={plant:[["植生配置V09・設計データ","MOSS_FOREST_A2_ECOLOGY_RELAYOUT_DESIGN_V09.json"],["植生統合・試作レビュー","https://github.com/celticmusic-nagoya/the-windbound-oath/pull/357#issuecomment-7038851582"]],tree:[["樹木V55・素材来歴","MOSS_FOREST_HERO_TREE_SOURCE_RECEIPT_V55.json"],["樹木V56・スキャン適応・LOD検証","MOSS_FOREST_HERO_TREE_SCAN_ADAPTATION_RECEIPT_V56.json"]],forest:[["林縁・経路設計V02","MOSS_FOREST_TRAIL_DESIGN_V02.json"],["谷・接合部V12","MOSS_FOREST_A2_JUNCTION_TOPOLOGY_RECEIPT_V12.json"],["写真PBR・配置V51","MOSS_FOREST_A2_PHOTO_PBR_RECEIPT_V51.json"],["地形追従経路V45D","MOSS_FOREST_CONFORMING_TRAIL_RECEIPT_V45D.json"],["南側排水V48B","MOSS_FOREST_A2_SOUTH_DRAINAGE_RECEIPT_V48B.json"]],river:[["断面模式図","RILDE_C02_C03_SECTION_HYDROLOGY_V01.svg"],["断面設計データ","RILDE_C02_C03_SECTION_HYDROLOGY_V01.json"],["河川網V26","RILDE_C03_RIVER_NETWORK_DESIGN_V26.json"],["中心部メッシュV27","RILDE_C03_RIVER_CORE_MESH_RECEIPT_V27.json"],["下流メッシュV28","RILDE_C03_LOWER_RIVER_MESH_RECEIPT_V28.json"],["水深・材質V34","RILDE_C03_DEPTH_WATER_RECEIPT_V34.json"],["局所河岸・森林接続V44","RILDE_C03_FOREST_TERRAIN_INTEGRATION_RECEIPT_V44.json"]],terrain:[["8エリア暫定平面図","RILDE_AREA_FIRST_PLAN_V03.svg"],["暫定平面データ","RILDE_AREA_FIRST_PLAN_V03.json"],["平面・縦横断面設計枠","RILDE_EIGHT_AREA_PLAN_SECTION_SLOTS_V01.svg"],["8エリア接続監査","RILDE_EIGHT_AREA_INTERFACE_RECONCILIATION_V01.json"]],sanctuary:[["聖域V58・景観候補記録","MOSS_FOREST_SANCTUARY_SCENIC_RECEIPT_V58.json"]],ruin:[["小遺跡V64・設計記録","MOSS_FOREST_SMALL_RUINS_BLUEPRINT_RECEIPT_V64.json"],["小遺跡V65・材質検証","MOSS_FOREST_SMALL_RUINS_MATERIAL_FRACTURE_RECEIPT_V65.json"],["小遺跡V66・操作検証","MOSS_FOREST_SMALL_RUINS_OPERATION_AUDIT_RECEIPT_V66.json"]]};
 function categoryButton(title,entries,click,designCount=0){
  const button=document.createElement("button");button.className="category-card";button.type="button";
  const cover=entries.find(e=>e.cover===true&&/\.(png|jpe?g)$/.test(e.path))||entries.find(e=>/\.(png|jpe?g)$/.test(e.path));
  if(cover){const img=document.createElement("img");img.src=base+cover.path;img.alt="";img.loading="lazy";button.append(img);}
  else {const placeholder=document.createElement("span");placeholder.className="category-placeholder";placeholder.textContent=designCount?"設計資料あり":"未同期";button.append(placeholder);}
  const label=document.createElement("strong");label.textContent=title;button.append(label);
  const count=document.createElement("small");count.textContent=entries.length+" 件"+(designCount?" ／ 設計 "+designCount+" 件":"");button.append(count);
  button.onclick=click;area.append(button);
 }
 function navigation(items){const nav=document.createElement("nav");nav.className="gallery-breadcrumb";nav.setAttribute("aria-label","成果物の階層");items.forEach((item,i)=>{if(i){const sep=document.createElement("span");sep.textContent=" / ";sep.setAttribute("aria-hidden","true");nav.append(sep);}if(item.action){const b=document.createElement("button");b.type="button";b.textContent=item.label;b.onclick=item.action;nav.append(b);}else{const current=document.createElement("strong");current.textContent=item.label;current.setAttribute("aria-current","page");nav.append(current);}});area.append(nav);}
 // Exact HEAD grouping: only published manifest entries, never infer a revision from a filename.
 function revisionHistory(){
  publishedGalleryView="history";
  area.replaceChildren();area.classList.remove("category-grid");
  navigation([{label:"制作領域",action:home},{label:"制作改訂履歴"}]);
  const back=document.createElement("button");back.type="button";back.className="category-back";back.textContent="← カテゴリ一覧";back.onclick=home;area.append(back);
  const note=document.createElement("p");note.textContent="公開済み成果物を完全なHEADで集約。QA・採用はmanifest申告であり、修正の因果関係・全履歴・独立QAは未保証。日時は成果物登録情報のみ。";note.style.gridColumn="1/-1";area.append(note);
  const revisions=new Map();
  for(const item of assigned){const head=/^[a-f0-9]{40}$/.test(item.entry.head||"")?item.entry.head:null;if(!revisions.has(head))revisions.set(head,[]);revisions.get(head).push(item);}
  const latest=items=>items.map(x=>typeof x.entry.created_at==="string"&&Number.isFinite(Date.parse(x.entry.created_at))?Date.parse(x.entry.created_at):-Infinity).reduce((a,b)=>Math.max(a,b),-Infinity);
  const ordered=[...revisions].sort((a,b)=>a[0]===null?1:b[0]===null?-1:latest(b[1])-latest(a[1])||a[0].localeCompare(b[0]));
  status.textContent="制作改訂履歴 / "+ordered.filter(([h])=>h!==null).length+" HEAD / "+valid.length+" 件";
  for(const [head,items] of ordered){
   const card=document.createElement("article");card.className="tile";card.dataset.revisionHead=head||"unknown";
   const title=document.createElement("h3");title.textContent=head?"HEAD "+head.slice(0,12):"HEAD未記録・不正値（改訂未確定）";card.append(title);
   const desc=document.createElement("p");desc.textContent=(head?"完全HEAD: "+head+" / ":"")+items.length+" 件 / "+(Number.isFinite(latest(items))?new Date(latest(items)).toISOString():"日時不明");card.append(desc);
   const counts=(key)=>{const map=new Map();for(const {entry} of items){const value=entry[key]||"未記録";map.set(value,(map.get(value)||0)+1);}return [...map].map(([k,n])=>k+": "+n).join(" / ");};
   for(const line of ["制作領域: "+[...new Set(items.map(x=>categories.find(([id])=>id===x.root)?.[1]||"その他"))].join(" / "),"QA: "+counts("qa"),"採用: "+counts("adoption")]){const p=document.createElement("p");p.textContent=line;card.append(p);}
   if(head){const link=document.createElement("a");link.href="https://github.com/celticmusic-nagoya/the-windbound-oath/commit/"+head;link.textContent="制作コミットを確認";card.append(link);}
   const button=document.createElement("button");button.type="button";button.textContent="この一覧の成果物を見る";button.onclick=()=>detail(null,head?"HEAD "+head.slice(0,12):"HEAD未確定",revisionHistory,items.map(x=>x.entry));card.append(button);area.append(card);
  }
 }
 function home(){
  publishedGalleryView="home";
  area.replaceChildren();area.classList.add("category-grid");
  navigation([{label:"制作領域"}]);
  status.textContent=valid.length+" 件 / カテゴリから閲覧";
  const recent=document.createElement("button");recent.type="button";recent.className="category-back";recent.textContent="全成果物・新着順";recent.onclick=()=>detail(null,"全成果物・新着順",home,valid);area.append(recent);
  const history=document.createElement("button");history.type="button";history.className="category-back";history.textContent="制作改訂履歴（HEAD別）";history.onclick=revisionHistory;area.append(history);
  for(const [id,title] of categories){categoryButton(title,groups.get(id),()=>id in subcategories?subhome(id,title):detail(id,title));}
 }
 function projectShortcut(id){
  if(!galleryProjectIds.has(id))return;
  const button=document.createElement("button");button.type="button";button.className="category-back";button.textContent="この領域の制作状況へ";
  button.onclick=()=>{
   const target=document.getElementById("project-"+id)?.querySelector("h3")||document.getElementById("projects-title");
   if(target){target.tabIndex=-1;target.focus({preventScroll:true});target.scrollIntoView({block:"start"});}
  };area.append(button);
 }
 function subhome(id,title){
  publishedGalleryView="sub";
  area.replaceChildren();area.classList.add("category-grid");
  navigation([{label:"制作領域",action:home},{label:title}]);
  const back=document.createElement("button");back.type="button";back.className="category-back";back.textContent="← カテゴリ一覧";back.onclick=home;area.append(back);
  projectShortcut(id);status.textContent=title+" / "+groups.get(id).length+" 件 / サブカテゴリ";
  if(id==="world"){const note=document.createElement("p");note.textContent="制作途中・未採用も掲載（権利・内容確認済みの画像）。画像未掲載の証跡は直近制作成果物から確認できます。";note.style.gridColumn="1/-1";area.append(note);const links=document.createElement("p");links.style.gridColumn="1/-1";for(const [label,path] of [["植生統合・樹木の制作記録","/actions/runs/44730162099"],["森林V21の制作記録","/actions/runs/45631347949"],["河川V26：EPA参照データ（CC BY 4.0・完成レンダーなし）","/actions/runs/45641788138"]]){const link=document.createElement("a");link.href="https://github.com/celticmusic-nagoya/the-windbound-oath"+path;link.textContent=label;link.rel="noopener noreferrer";links.append(link,document.createTextNode("　"));}area.append(links);}
  categoryButton(title+" / 全件",groups.get(id),()=>detail(id,title+" / 全件",()=>subhome(id,title)));
  for(const [sub,label] of subcategories[id]){
   const entries=assigned.filter(x=>x.root===id&&x.sub===sub).map(x=>x.entry);
   categoryButton(label,entries,()=>detail(id,title+" / "+label,()=>subhome(id,title),entries,id==="world"?sub:null),id==="world"?(worldDesign[sub]?.length||0):0);
  }
 }
 function detail(id,title,goBack=home,subset=null,designKey=null){
 publishedGalleryView="detail";
 area.replaceChildren();area.classList.remove("category-grid");
 navigation([{label:"制作領域",action:home},{label:title}]);
 const back=document.createElement("button");back.type="button";back.className="category-back";back.textContent="← カテゴリ一覧";back.onclick=goBack;area.append(back);
 projectShortcut(id);
 const entries=[...(subset||groups.get(id))].sort((a,b)=>String(b.created_at||"").localeCompare(String(a.created_at||"")));status.textContent=title+" / "+entries.length+" 件 / 制作成果物";
 if(designKey&&worldDesign[designKey]){
  const docs=document.createElement("section");docs.className="gallery-design-links";docs.dataset.designCategory=designKey;
  const heading=document.createElement("h3");heading.textContent="設計図・設計データ";docs.append(heading);
  const note=document.createElement("p");note.textContent="設計候補・制作記録。画像件数とは別計上。実測・採用・完成を意味しません。";docs.append(note);
  for(const [label,path] of worldDesign[designKey]){const link=document.createElement("a");link.textContent=label;link.href=path.startsWith("https://")?path:"https://github.com/celticmusic-nagoya/the-windbound-oath/blob/3440af1b22a9c87c55237bab25921aa20aa80d34/docs/production/region_master/"+path;link.rel="noopener noreferrer";docs.append(link);}
  area.append(docs);
 }
 const photos=entries.filter(e=>/\.(png|jpe?g)$/.test(e.path));
 if(photos.length>=2){
 const compare=document.createElement("button");compare.type="button";compare.className="category-back";compare.textContent="画像比較";area.append(compare);
 compare.onclick=()=>{
 const dialog=document.createElement("dialog");dialog.className="gallery-lightbox";
 const close=document.createElement("button");close.textContent="閉じる";close.onclick=()=>dialog.close();dialog.append(close);
 const note=document.createElement("p");note.textContent="カテゴリ内の全画像から表示比較。同一カメラ・縮尺・照明は未保証。";dialog.append(note);
 const pair=document.createElement("div");pair.style.cssText="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%";
 const controls=[];
 for(let i=0;i<2;i++){
 const panel=document.createElement("div");panel.style.minWidth="0";
 const select=document.createElement("select");select.style.width="100%";select.setAttribute("aria-label",i?"比較B":"比較A");
 photos.forEach((e,j)=>{const o=document.createElement("option");o.value=String(j);o.textContent=(e.stage||"未分類")+" / "+e.name;select.append(o);});
 const img=document.createElement("img");img.style.cssText="width:100%;height:clamp(160px,38vh,480px);object-fit:contain";
 const info=document.createElement("p");info.style.overflowWrap="anywhere";info.style.fontSize="0.8rem";
 select.value=String(i===0?0:Math.max(1,photos.findIndex(e=>e.name===photos[0].name&&e.artifact_id!==photos[0].artifact_id)));
 const update=()=>{const e=photos[Number(select.value)];img.src=base+e.path;img.alt=e.name;info.textContent=(e.stage||"未分類")+" / "+(e.created_at||"日時不明")+" / QA: "+e.qa+" / 採用: "+e.adoption+" / HEAD: "+(e.head||"未記録")+" / SHA-256: "+e.sha256+" / run: "+(e.run_id??"未記録")+" / Artifact: "+(e.artifact_id??"未記録");};
 select.onchange=update;update();controls.push(select);panel.append(select,img,info);pair.append(panel);
 }
 dialog.append(pair);dialog.addEventListener("close",()=>dialog.remove());document.body.append(dialog);dialog.showModal();
 };
 }
 const stages=[...new Set(entries.map(e=>e.stage||"未分類"))];
 const filter=document.createElement("select");filter.className="category-back";filter.setAttribute("aria-label","制作段階");for(const name of ["すべて",...stages]){const opt=document.createElement("option");opt.value=name;opt.textContent=name;filter.append(opt);}area.append(filter);
 const search=document.createElement("input");search.type="search";search.placeholder="画像名・制作段階・QAで検索";search.setAttribute("aria-label","成果物検索");search.className="gallery-search";area.append(search);
 const makeFilter=(label,key)=>{const select=document.createElement("select");select.className="category-back";select.setAttribute("aria-label",label);const all=document.createElement("option");all.value="";all.textContent=label+"：すべて";select.append(all);const values=[...new Set(entries.map(e=>e[key]))].sort();values.forEach((v,i)=>{const opt=document.createElement("option");opt.value=String(i);opt.textContent=v||"未記録";select.append(opt);});area.append(select);return {select,values};};
 const qaFilter=makeFilter("QA状態","qa"),adoptionFilter=makeFilter("採用状態","adoption");
 const matches=e=>(filter.value==="すべて"||(e.stage||"未分類")===filter.value)&&(qaFilter.select.value===""||e.qa===qaFilter.values[Number(qaFilter.select.value)])&&(adoptionFilter.select.value===""||e.adoption===adoptionFilter.values[Number(adoptionFilter.select.value)])&&[e.name,e.stage,e.qa,e.adoption,e.head,e.run_id,e.artifact_id].join(" ").toLowerCase().includes(search.value.trim().toLowerCase());
 const clear=document.createElement("button");clear.type="button";clear.className="category-back";clear.textContent="絞り込み解除";clear.onclick=()=>{filter.value="すべて";qaFilter.select.value="";adoptionFilter.select.value="";search.value="";apply();};area.append(clear);
 const tiles=[];
 for(const e of entries){const tile=renderEntry(e);tiles.push({tile,e});const img=tile.querySelector("img");if(img){const open=document.createElement("button");open.type="button";open.className="gallery-image-button";open.setAttribute("aria-label",e.name+" を拡大");img.replaceWith(open);open.append(img);open.onclick=()=>{
 const visiblePhotos=photos.filter(matches);
 let index=visiblePhotos.indexOf(e);if(index<0)return;
 const dialog=document.createElement("dialog");dialog.className="gallery-lightbox";dialog.setAttribute("aria-label","成果物画像レビュー");
 const bar=document.createElement("div");bar.style.cssText="display:flex;gap:8px;align-items:center;flex-wrap:wrap";
 const control=(label,action)=>{const button=document.createElement("button");button.type="button";button.textContent=label;button.style.minHeight="44px";button.onclick=action;bar.append(button);return button;};
 const close=control("閉じる",()=>dialog.close());
 const prev=control("← 前へ",()=>move(-1)),next=control("次へ →",()=>move(1));
 const count=document.createElement("span");count.setAttribute("role","status");bar.append(count);
 const heading=document.createElement("h3");heading.style.overflowWrap="anywhere";
 const viewport=document.createElement("div");viewport.setAttribute("role","region");viewport.setAttribute("aria-label","画像拡大表示");viewport.tabIndex=0;viewport.style.cssText="width:100%;max-height:58vh;overflow:auto;overscroll-behavior:contain";
 const full=document.createElement("img");full.style.cssText="display:block;width:100%;max-height:58vh;object-fit:contain";viewport.append(full);
 let zoom=1;
 const zoomOut=control("縮小",()=>setZoom(zoom-0.5)),zoomIn=control("拡大",()=>setZoom(zoom+0.5)),reset=control("全体表示",()=>setZoom(1));
 const zoomLabel=document.createElement("span");zoomLabel.setAttribute("aria-label","拡大率");bar.append(zoomLabel);
 function setZoom(value){zoom=Math.max(1,Math.min(4,value));full.style.width=(zoom*100)+"%";full.style.maxWidth=zoom===1?"100%":"none";full.style.maxHeight=zoom===1?"58vh":"none";zoomLabel.textContent=Math.round(zoom*100)+"%";zoomOut.disabled=zoom===1;zoomIn.disabled=zoom===4;reset.disabled=zoom===1;if(zoom===1){viewport.scrollTop=0;viewport.scrollLeft=0;}}

 const info=document.createElement("details");const summary=document.createElement("summary");summary.textContent="制作情報・QA・来歴";const meta=document.createElement("p");meta.className="gallery-review-metadata";meta.style.overflowWrap="anywhere";const provenancePanel=document.createElement("div");info.append(summary,meta,provenancePanel);
 const original=document.createElement("a");original.textContent="元画像を開く";original.target="_blank";original.rel="noopener noreferrer";
 function update(){const p=visiblePhotos[index];heading.textContent=p.name;setZoom(1);full.src=base+p.path;full.alt=p.name;original.href=full.src;count.textContent=(index+1)+" / "+visiblePhotos.length;prev.disabled=index===0;next.disabled=index===visiblePhotos.length-1;meta.textContent="制作段階: "+(p.stage||"未分類")+" / QA: "+p.qa+" / 採用: "+p.adoption+" / HEAD: "+(p.head||"未記録")+" / SHA-256: "+p.sha256+" / run: "+(p.run_id??"未記録")+" / Artifact: "+(p.artifact_id??"未記録");provenancePanel.replaceChildren();provenance(p,provenancePanel);}
 function move(delta){const target=index+delta;if(target>=0&&target<visiblePhotos.length){index=target;update();}}
 dialog.addEventListener("keydown",event=>{if(event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||viewport.contains(event.target))return;if(event.key==="ArrowLeft"||event.key==="ArrowRight"){event.preventDefault();move(event.key==="ArrowLeft"?-1:1);}});
 dialog.append(bar,heading,viewport,original,info);update();dialog.addEventListener("close",()=>{dialog.remove();if(open.isConnected)open.focus();});document.body.append(dialog);dialog.showModal();close.focus();
 };}area.append(tile);}
 const empty=document.createElement("p");empty.textContent="条件に一致する成果物はありません。";empty.hidden=true;area.append(empty);
 const apply=()=>{let count=0;for(const {tile,e} of tiles){tile.hidden=!matches(e);if(!tile.hidden)count++;}empty.hidden=count!==0||entries.length===0;status.textContent=title+" / 表示 "+count+" 件・全 "+entries.length+" 件";};filter.onchange=apply;search.oninput=apply;qaFilter.select.onchange=apply;adoptionFilter.select.onchange=apply;
 if(!entries.length){filter.hidden=true;search.hidden=true;qaFilter.select.hidden=true;adoptionFilter.select.hidden=true;clear.hidden=true;const p=document.createElement("p");p.textContent="成果物はまだ同期されていません。";area.append(p);}
 }
 openGalleryCategory=id=>{const category=categories.find(([key])=>key===id);if(category){const title=category[1];if(id in subcategories)subhome(id,title);else detail(id,title);}};
 if(pendingGalleryCategory){const id=pendingGalleryCategory;pendingGalleryCategory=null;openGalleryCategory(id);}else home();
 }catch(e){if(generation===publishedGalleryGeneration){if(openGalleryCategory)pendingGalleryCategory=null;publishedGalleryLive.textContent="更新失敗: "+e.message+" / 前回取得分を保持。";if(publishedGalleryKey===null)status.textContent="同期一覧未取得: "+e.message;}}
 finally{publishedGalleryActive--;if(generation===publishedGalleryGeneration)publishedGalleryDue=Date.now()+(success?60000:300000);schedulePublishedGallery();}
}
document.getElementById("refresh-published").addEventListener("click",()=>loadPublishedGallery(false));
document.addEventListener("visibilitychange",schedulePublishedGallery);
loadPublishedGallery();
