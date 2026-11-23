"use strict";
// Read-only owner/handoff dashboard. GitHub PR metadata is NOT lease/fencing evidence.
(() => {
 const repo="celticmusic-nagoya/the-windbound-oath";
 const api="https://api.github.com/repos/"+repo;
 const owners=[
  {id:468,name:"Codex｜長時間制作エンジン",scope:"Factory / Session / CAS・fencing"},
  {id:485,name:"Claude｜設計図エンジン",scope:"Blueprint Engine / 残差判定 / #468契約連携"},
  {id:427,name:"キャラクター担当｜モルウェン",scope:"実設計図 / VRoid / 3D制作"},
  {id:421,name:"マップ担当｜風待ちの崖",scope:"崖の実設計図 / Blender制作"},
  {id:364,name:"マップ担当｜地域統合",scope:"村・建築・地域統合"},
  {id:484,name:"ChatGPT｜Production Studio",scope:"読み取り専用UI / 成果物可視化 / 独立QA"}
 ];
 const area=document.getElementById("handoff-cards");
 const status=document.getElementById("handoff-status");
 const button=document.getElementById("handoff-refresh");
 let generation=0;
 if(!area||!status||!button)return;
 const el=(tag,content)=>{const n=document.createElement(tag);n.textContent=content;return n;};
 async function get(path){
  const response=await fetch(api+path,{headers:{Accept:"application/vnd.github+json"},credentials:"omit",cache:"no-store",signal:AbortSignal.timeout(10000)});
  if(!response.ok){
   const limited=response.status===403||response.status===429;
   throw new Error(limited?"GitHub API制限またはアクセス拒否 (HTTP "+response.status+")":"HTTP "+response.status);
  }
  const data=await response.json();
  if(!data||typeof data!=="object"||!data.head||typeof data.head.sha!=="string"||!/^([0-9a-f]{40})$/i.test(data.head.sha)||!["open","closed"].includes(data.state)){
   throw new Error("GitHub PR応答形式を検証できません");
  }
  return data;
 }
 function addCard(owner,result){
  const card=el("article","");card.className="tile handoff-card";
  card.append(el("h3",owner.name),el("p","担当範囲: "+owner.scope));
  if(result.status==="fulfilled"){
   const p=result.value;
   card.append(el("p","PR #"+owner.id+" / "+(p.merged?"merged":p.state)+(p.draft?" / Draft":"")),
    el("p","HEAD: "+(p.head?.sha||"UNKNOWN")),
    el("p","PR更新: "+(p.updated_at||"UNKNOWN")),
    el("p","参照元: GitHub REST API（公開PR情報のみ）"));
  }else {
   const reason=result.reason;
   const timedOut=reason?.name==="TimeoutError"||reason?.name==="AbortError";
   card.append(el("p","PR取得失敗: "+(timedOut?"10秒でタイムアウト":String(reason?.message||reason))));
  }
  card.append(el("p","注意: PR更新時刻は担当の停止・応答・lease更新を証明しません。"));
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
  const current=++generation;
  button.disabled=true;status.textContent="PR情報取得中 / lease・STOP_ACKは検証対象外";area.replaceChildren();
  try{
   const results=await Promise.allSettled(owners.map(o=>get("/pulls/"+o.id)));
   if(current!==generation)return;
   owners.forEach((o,i)=>addCard(o,results[i]));
   const failures=results.filter(r=>r.status==="rejected").length;
   status.textContent="PR取得 "+(owners.length-failures)+"/"+owners.length+(failures?" / 取得失敗 "+failures+"件（未検証）":"")+" / "+new Date().toLocaleString("ja-JP")+
    " / 書き込み可否は全件SYNC_UNVERIFIED";
  }catch(e){if(current===generation)status.textContent="取得失敗: "+e.message;}
  finally{if(current===generation)button.disabled=false;}
 }
 button.addEventListener("click",refresh);
 refresh();
})();
