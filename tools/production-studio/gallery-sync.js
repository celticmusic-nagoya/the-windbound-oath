"use strict";
async function loadPublishedGallery(){
 const area=document.getElementById("published-gallery"), status=document.getElementById("published-status");
 area.replaceChildren();
 try{
 let base="./";
 let response;
 if(location.hostname==="celticmusic-nagoya.github.io"){
 const remote="https://raw.githubusercontent.com/celticmusic-nagoya/the-windbound-oath/studio-published/";
 try{response=await fetch(remote+"gallery-manifest.json",{cache:"no-store",credentials:"omit",signal:AbortSignal.timeout(8000)});if(response.ok)base=remote;}catch{}
 }
 if(!response?.ok)response=await fetch("./gallery-manifest.json",{cache:"no-store",credentials:"omit"});
 if(!response.ok)throw Error("HTTP "+response.status);
 const manifest=await response.json();
 if(manifest.version!==1||!Array.isArray(manifest.entries)||manifest.entries.length>500)throw Error("一覧形式不正");
 const valid=[];
 for(const e of manifest.entries){
 if(!/^[a-f0-9]{64}$/.test(e.sha256)||!new RegExp("^published/"+e.sha256+"\\.(png|jpg|jpeg|glb|vrm)$").test(e.path)||!Number.isSafeInteger(e.bytes)||e.bytes<1||e.bytes>64*1024*1024)continue;
 valid.push(e);
 }
 function renderEntry(e){
 const tile=document.createElement("article");tile.className="tile";
 const label=document.createElement("p");label.textContent=e.name+" / QA: "+e.qa+" / 採用: "+e.adoption;tile.append(label);
 const source=document.createElement("a");source.href="https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/"+Number(e.run_id)+"/artifacts/"+Number(e.artifact_id);source.textContent="生成元 Artifact";tile.append(source);
 if(/\.(png|jpe?g)$/.test(e.path)){const img=document.createElement("img");img.src=base+e.path;img.loading="lazy";img.alt=e.name;tile.prepend(img);}
 else {const button=document.createElement("button");button.textContent="3D表示";button.onclick=async()=>{button.disabled=true;try{const res=await fetch(base+e.path,{credentials:"omit"});if(!res.ok)throw Error("HTTP "+res.status);const reader=res.body.getReader();let size=0;const parts=[];try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>e.bytes)throw Error("容量不一致");parts.push(value);}}finally{await reader.cancel();}const blob=new Blob(parts);const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",await blob.arrayBuffer())),x=>x.toString(16).padStart(2,"0")).join("");if(size!==e.bytes||hash!==e.sha256)throw Error("SHA不一致");const input=document.getElementById("model-file"),dt=new DataTransfer();dt.items.add(new File([blob],e.path.split("/").pop()));input.files=dt.files;input.dispatchEvent(new Event("change"));document.getElementById("model-view").scrollIntoView({block:"center"});}catch(err){status.textContent="モデル取得失敗: "+err.message;}finally{button.disabled=false;}};tile.append(button);}
 return tile;
 }
 const categories=[["cliff","風待ちの崖"],["morwen","モルウェン"],["village","リルド村"],["other","その他"]];
 const category=e=>categories.some(([id])=>id===e.category)?e.category:e.run_id===44708204132?"cliff":"other";
 const groups=new Map(categories.map(([id])=>[id,valid.filter(e=>category(e)===id)]));
 function home(){
 area.replaceChildren();area.classList.add("category-grid");
 status.textContent=valid.length+" 件 / カテゴリから閲覧";
 for(const [id,title] of categories){
 const entries=groups.get(id), button=document.createElement("button");
 button.className="category-card";button.type="button";
 const cover=entries.find(e=>e.cover===true&&/\.(png|jpe?g)$/.test(e.path))||entries.find(e=>/\.(png|jpe?g)$/.test(e.path));
 if(cover){const img=document.createElement("img");img.src=base+cover.path;img.alt="";img.loading="lazy";button.append(img);}
 else {const placeholder=document.createElement("span");placeholder.className="category-placeholder";placeholder.textContent="未同期";button.append(placeholder);}
 const label=document.createElement("strong");label.textContent=title;button.append(label);
 const count=document.createElement("small");count.textContent=entries.length+" 件";button.append(count);
 button.onclick=()=>detail(id,title);area.append(button);
 }
 }
 function detail(id,title){
 area.replaceChildren();area.classList.remove("category-grid");
 const back=document.createElement("button");back.type="button";back.className="category-back";back.textContent="← カテゴリ一覧";back.onclick=()=>home();area.append(back);
 const entries=groups.get(id);status.textContent=title+" / "+entries.length+" 件 / 公開用候補";
 const stages=[...new Set(entries.map(e=>e.stage||"未分類"))];
 const filter=document.createElement("select");filter.className="category-back";filter.setAttribute("aria-label","制作段階");for(const name of ["すべて",...stages]){const opt=document.createElement("option");opt.value=name;opt.textContent=name;filter.append(opt);}area.append(filter);
 for(const e of entries){const tile=renderEntry(e);tile.dataset.stage=e.stage||"未分類";const img=tile.querySelector("img");if(img){const open=document.createElement("button");open.type="button";open.className="gallery-image-button";open.setAttribute("aria-label",e.name+" を拡大");img.replaceWith(open);open.append(img);open.onclick=()=>{const dialog=document.createElement("dialog");const close=document.createElement("button");close.textContent="閉じる";close.onclick=()=>dialog.close();const full=document.createElement("img");full.src=base+e.path;full.alt=e.name;dialog.className="gallery-lightbox";dialog.append(close,full);dialog.addEventListener("close",()=>dialog.remove());document.body.append(dialog);dialog.showModal();};}area.append(tile);}
 filter.onchange=()=>{for(const tile of area.querySelectorAll("article"))tile.hidden=filter.value!=="すべて"&&tile.dataset.stage!==filter.value;};
 if(!entries.length){filter.hidden=true;const p=document.createElement("p");p.textContent="公開用成果物はまだ同期されていません。";area.append(p);}
 }
 home();
 }catch(e){status.textContent="同期一覧未取得: "+e.message;}
}
document.getElementById("refresh-published").addEventListener("click",loadPublishedGallery);
loadPublishedGallery();
