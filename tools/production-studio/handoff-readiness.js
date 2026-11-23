"use strict";
// Read-only owner/handoff dashboard. GitHub PR metadata is NOT lease/fencing evidence.
(() => {
 const repo="celticmusic-nagoya/the-windbound-oath";
 const api="https://api.github.com/repos/"+repo;
 const owners=[
  {id:468,name:"Codex｜長時間制作エンジン",scope:"Factory / Session / CAS・fencing"},
  {id:427,name:"キャラクター担当｜モルウェン",scope:"実設計図 / VRoid / 3D制作"},
  {id:421,name:"マップ担当｜風待ちの崖",scope:"崖の実設計図 / Blender制作"},
  {id:364,name:"マップ担当｜地域統合",scope:"村・建築・地域統合"}
 ];
 const area=document.getElementById("handoff-cards");
 const status=document.getElementById("handoff-status");
 const button=document.getElementById("handoff-refresh");
 if(!area||!status||!button)return;
 const el=(tag,content)=>{const n=document.createElement(tag);n.textContent=content;return n;};
 async function get(path){
  const response=await fetch(api+path,{headers:{Accept:"application/vnd.github+json"},credentials:"omit",cache:"no-store"});
  if(!response.ok)throw new Error("HTTP "+response.status);
  return response.json();
 }
 function addCard(owner,result){
  const card=el("article","");card.className="tile handoff-card";
  card.append(el("h3",owner.name),el("p","担当範囲: "+owner.scope));
  if(result.status==="fulfilled"){
   const p=result.value;
   card.append(el("p","PR #"+owner.id+" / "+(p.merged?"merged":p.state)+(p.draft?" / Draft":"")),
    el("p","HEAD: "+(p.head?.sha||"UNKNOWN")),
    el("p","PR更新: "+(p.updated_at||"UNKNOWN")));
  }else card.append(el("p","PR取得失敗: "+String(result.reason?.message||result.reason)));
  const link=el("a","担当PR・最新指示を確認");link.href="https://github.com/"+repo+"/pull/"+owner.id;link.rel="noopener noreferrer";card.append(link);
  const checklist=el("dl","");
  const fields=[
   ["STOP_ACK","未検証"],["lease / fencing","未検証"],["checkpoint SHA・別run復元","未検証"],
   ["全イベントActions・Artifacts","未検証"],["G1〜G4","未検証"]
  ];
  for(const [key,value] of fields){checklist.append(el("dt",key),el("dd",value));}
  card.append(checklist,el("p","代行書き込み: SYNC_UNVERIFIED（自動切替不可）"));
  area.append(card);
 }
 async function refresh(){
  button.disabled=true;status.textContent="PR情報取得中 / lease・STOP_ACKは検証対象外";area.replaceChildren();
  try{
   const results=await Promise.allSettled(owners.map(o=>get("/pulls/"+o.id)));
   owners.forEach((o,i)=>addCard(o,results[i]));
   const failures=results.filter(r=>r.status==="rejected").length;
   status.textContent="PR取得 "+(owners.length-failures)+"/"+owners.length+" / "+new Date().toLocaleString("ja-JP")+
    " / 書き込み可否は全件SYNC_UNVERIFIED";
  }catch(e){status.textContent="取得失敗: "+e.message;}
  finally{button.disabled=false;}
 }
 button.addEventListener("click",refresh);
 refresh();
})();
