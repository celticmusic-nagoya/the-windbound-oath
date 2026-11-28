"use strict";
(() => {
const REPO="celticmusic-nagoya/the-windbound-oath",LIMIT=128*1024*1024,JSON_LIMIT=16384;
const get=id=>document.getElementById(id);
const zipInput=get("artifact-zip"),expected=get("artifact-digest"),verify=get("verify-artifact"),result=get("verify-result");
const input=get("artifact-locator"),clear=get("artifact-locator-clear"),status=get("artifact-locator-status"),source=get("artifact-locator-source");
let generation=0,mode="manual",locator=null,busy=false;
const id=n=>Number.isSafeInteger(n)&&n>0;
const label=s=>typeof s==="string"&&s.length>0&&s.length<=180&&!/[\x00-\x1f\x7f]/.test(s);
const time=s=>typeof s==="string"&&s.length<=40&&Number.isFinite(Date.parse(s));
function invalid(){throw Error("復元情報の形式・制作元・識別情報が不正です");}
function readLocator(x){
 if(!x||Array.isArray(x)||typeof x!=="object"||x.schema!=="two.studio.artifact-locator.v1"||x.repository!==REPO||
 !id(x.artifact_id)||!id(x.run_id)||!id(x.archive_bytes)||!label(x.name)||!label(x.head_branch)||
 typeof x.head_sha!=="string"||!/^[a-f0-9]{40}$/.test(x.head_sha)||!(x.archive_digest===null||typeof x.archive_digest==="string"&&/^sha256:[a-f0-9]{64}$/.test(x.archive_digest))||
 !time(x.metadata_observed_at)||!(x.created_at===null||time(x.created_at))||!(x.expires_at===null||time(x.expires_at))||
 x.preservation_status!=="UNVERIFIED"||x.byte_verification!=="NOT_RUN"||x.adoption!=="UNDETERMINED")invalid();
 const url="https://github.com/"+REPO+"/actions/runs/"+x.run_id+"/artifacts/"+x.artifact_id;
 if(x.original_artifact_url!==url)invalid();
 return {name:x.name,id:x.artifact_id,run:x.run_id,head:x.head_sha,bytes:x.archive_bytes,digest:x.archive_digest,observed:x.metadata_observed_at,expiry:x.expires_at,url};
}
function controls(){
 zipInput.disabled=busy;input.disabled=busy;clear.disabled=busy;
 expected.disabled=busy||mode!=="manual";
 verify.disabled=busy||mode==="loading"||mode==="invalid"||(mode==="locator"&&(!locator?.digest||locator.bytes>LIMIT));
}
// Global Studio anchor CSS sets display:block; enforce hidden state explicitly.
function hideSource(){source.hidden=true;source.style.display="none";source.removeAttribute("href");}
function manual(digest=""){
 ++generation;locator=null;mode="manual";input.value="";expected.value=digest;hideSource();status.textContent="復元情報未選択・手動SHA照合";result.textContent="未照合";controls();
}
clear.addEventListener("click",()=>{if(!busy)manual();});
window.addEventListener("studio-artifact-target",e=>{
 if(busy)return;
 const digest=e.detail?.digest;
 if(typeof digest!=="string"||!(/^[a-f0-9]{64}$/.test(digest)||digest===""))return;
 zipInput.value="";zipInput.dispatchEvent(new Event("change"));manual(digest);
});
input.addEventListener("change",async()=>{
 if(busy)return;
 const token=++generation,f=input.files[0];
 locator=null;expected.value="";hideSource();result.textContent="未照合";
 if(!f){manual();return;}
 mode="loading";status.textContent="復元情報を検査中";controls();
 try{
  if(f.size===0||f.size>JSON_LIMIT)throw Error("JSONは16 KiB以内");
  const x=readLocator(JSON.parse(await f.text()));
  if(token!==generation)return;
  locator=x;mode="locator";expected.value=x.digest?x.digest.slice(7):"";
  source.href=x.url;source.hidden=false;source.style.removeProperty("display");
  const expiry=x.expiry?(Date.parse(x.expiry)<=Date.now()?"期限経過（取得可否未確認）":"記録期限 "+new Date(x.expiry).toLocaleString("ja-JP")):"期限不明";
  status.textContent="復元情報読込: "+x.name+" / Run "+x.run+" / Artifact "+x.id+" / HEAD "+x.head+" / "+x.bytes.toLocaleString("ja-JP")+" bytes / "+expiry+" / 記録時刻 "+x.observed+" / 発行者未認証・保全未確認"+(!x.digest?" / SHAなし：照合不可":x.bytes>LIMIT?" / 128 MiB上限超過：端末内照合不可":"");
 }catch(e){
  if(token!==generation)return;
  mode="invalid";status.textContent="復元情報読込失敗: "+e.message+"。クリアまたは正しいJSONを選択。";
 }finally{if(token===generation)controls();}
});
verify.addEventListener("click",async()=>{
 if(busy||mode==="loading"||mode==="invalid")return;
 const file=zipInput.files[0],pin=mode==="locator"?locator:null;
 const digest=pin?pin.digest?.slice(7):expected.value.trim().toLowerCase().replace(/^sha256:/,"");
 if(!file||!digest||!/^[a-f0-9]{64}$/.test(digest)){result.textContent="ZIPと配布元SHA-256を指定してください";return;}
 if(file.size>LIMIT){result.textContent="128 MiB上限超過（端末メモリ保護）";return;}
 if(pin&&file.size!==pin.bytes){result.textContent="FAIL: 復元情報の容量と不一致 / "+file.size+" bytes（期待 "+pin.bytes+" bytes）";return;}
 if(!globalThis.crypto?.subtle){result.textContent="HTTPSまたはlocalhostが必要です";return;}
 busy=true;controls();result.textContent="照合中";
 try{
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",await file.arrayBuffer())),x=>x.toString(16).padStart(2,"0")).join("");
  result.textContent=(hash===digest?(pin?"PASS: 復元情報の容量・SHA一致":"PASS: 指定digestと一致"):(pin?"FAIL: 復元情報のSHA不一致":"FAIL: 指定digestと不一致"))+" / "+file.name+" / "+hash+(pin?" / 記録とのバイト一致のみ・発行者認証／ZIP内部／保全／原本再読込／品質は未確認":" / 来歴・内容・品質は別途確認");
 }catch(e){result.textContent="照合失敗: "+e.message;}
 finally{busy=false;controls();}
});
zipInput.addEventListener("change",()=>{if(!busy)result.textContent="未照合";});
expected.addEventListener("input",()=>{if(!busy)result.textContent="未照合";});
hideSource();controls();
})();
