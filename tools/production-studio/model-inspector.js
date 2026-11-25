"use strict";
function inspectGlb(buffer){
 const v=new DataView(buffer);if(v.byteLength<20||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==v.byteLength)throw Error("GLB 2.0 header invalid");
 let offset=12,doc=null;while(offset<v.byteLength){if(offset+8>v.byteLength)throw Error("Incomplete chunk header");const n=v.getUint32(offset,true),kind=v.getUint32(offset+4,true);offset+=8;if(n%4||n>v.byteLength-offset)throw Error("Invalid chunk length");if(doc===null){if(kind!==0x4e4f534a||n>8*1024*1024)throw Error("Invalid JSON chunk");doc=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(new Uint8Array(buffer,offset,n)));}offset+=n;}
 if(!doc||doc.asset?.version!=="2.0")throw Error("Unsupported glTF asset");const extensions=doc.extensions||{},vrm=extensions.VRMC_vrm,old=extensions.VRM;return {format:vrm?"VRM 1.0":old?"VRM 0.x":"GLB",meshes:doc.meshes?.length||0,materials:doc.materials?.length||0,animations:doc.animations?.length||0,skins:doc.skins?.length||0,images:doc.images?.length||0,humanoidBones:vrm?Object.keys(vrm.humanoid?.humanBones||{}).length:old?(old.humanoid?.humanBones?.length||0):null,expressions:vrm?Object.keys(vrm.expressions?.preset||{}).length+Object.keys(vrm.expressions?.custom||{}).length:old?(old.blendShapeMaster?.blendShapeGroups?.length||0):null,externalResources:[...(doc.buffers||[]),...(doc.images||[])].some(x=>typeof x.uri==="string"&&!x.uri.startsWith("data:"))};
}
if(typeof document!=="undefined"){const input=document.getElementById("model-file"),out=document.getElementById("model-status");let generation=0;input.addEventListener("change",async()=>{const id=++generation,f=input.files[0];if(!f){out.textContent="未選択";return;}if(f.size>100*1024*1024){out.textContent="100 MiB上限超過";return;}out.textContent="検査中";try{const m=inspectGlb(await f.arrayBuffer());if(id!==generation)return;out.textContent=f.name+" / "+m.format+" / メッシュ "+m.meshes+" / 材質 "+m.materials+" / アニメーション "+m.animations+" / スキン "+m.skins+" / 画像 "+m.images+(m.humanoidBones===null?"":" / humanoid宣言 "+m.humanoidBones+" / 表情宣言 "+m.expressions)+" / "+(m.externalResources?"外部参照あり（取得しない）":"外部参照なし")+" / 構造概要のみ・描画未検証";}catch(e){if(id===generation)out.textContent="検査失敗: "+e.message;}});}

// Local byte identity check for native transfer. No parsing, rendering, uploading or network fetch.
(() => {
 if(typeof document==="undefined")return;
 const host=document.getElementById("model-status");if(!host)return;
 const make=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;return el;};
 const panel=make("section","");panel.id="native-sha-panel";panel.className="tile";
 panel.append(make("h3","VRoid・VRM・Blender原本のSHA-256照合"),make("p","取得済み原本と、信頼できる生成／保全記録のSHAを端末内で照合します。形式・ライセンス・再読込・G1〜G4は別途検証。最大100 MiB。ファイル送信なし。"));
 const source=make("a","VRM→Blender移行担当 PR #570");source.href="https://github.com/celticmusic-nagoya/the-windbound-oath/pull/570";source.rel="noopener noreferrer";panel.append(source);
 const file=make("input","");file.id="native-sha-file";file.type="file";file.accept=".vroid,.vrm,.blend,.glb";
 const fileLabel=make("label","照合するモデル原本");fileLabel.htmlFor=file.id;
 const expected=make("input","");expected.id="native-sha-expected";expected.type="text";expected.autocomplete="off";expected.spellcheck=false;expected.style.maxWidth="100%";
 const label=make("label","記録されたSHA-256");label.htmlFor=expected.id;
 const verify=make("button","原本を端末内で照合");verify.id="native-sha-verify";verify.type="button";
 const out=make("p","未照合");out.id="native-sha-result";out.setAttribute("role","status");out.style.overflowWrap="anywhere";
 panel.append(fileLabel,file,label,expected,verify,out);host.before(panel);
 let busy=false;
 const reset=()=>{out.textContent="未照合";};file.addEventListener("change",reset);expected.addEventListener("input",reset);
 verify.addEventListener("click",async()=>{
  if(busy)return;
  const f=file.files[0],digest=expected.value.trim().toLowerCase().replace(/^sha256:/,"");
  if(!f||!(/\.(vroid|vrm|blend|glb)$/i.test(f.name))||!/^[0-9a-f]{64}$/.test(digest)){out.textContent="対象形式のファイルとSHA-256を指定してください";return;}
  if(f.size>100*1024*1024||f.size===0){out.textContent="空ファイルまたは100 MiB上限超過";return;}
  if(!globalThis.crypto?.subtle){out.textContent="HTTPSまたはlocalhostが必要です";return;}
  busy=true;file.disabled=expected.disabled=verify.disabled=true;out.textContent="照合中";
  try{const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",await f.arrayBuffer())),x=>x.toString(16).padStart(2,"0")).join("");
   out.textContent=(hash===digest?"PASS: 指定SHA一致":"FAIL: 指定SHA不一致")+" / "+f.name+" / "+f.size+" bytes / "+hash+" / バイト照合のみ・再読込未検証";
  }catch(e){out.textContent="照合失敗: "+e.message;}
  finally{busy=false;file.disabled=expected.disabled=verify.disabled=false;}
 });
})();
