(() => {
"use strict";
const get=id=>document.getElementById(id);
const inputs=["audio-source","audio-candidate","audio-receipt"].map(get);
const players=["audio-a","audio-b"].map(get);
const check=get("audio-check"), clear=get("audio-clear"), status=get("audio-status"), results=get("audio-results");
let generation=0, urls=[], last=0;
const hex=/^[a-f0-9]{64}$/;
function invalid(message){throw new Error(message);}
function reset(){
  generation++;
  for(const a of players){a.pause();a.removeAttribute("src");a.load();}
  for(const url of urls)URL.revokeObjectURL(url);
  urls=[];last=0;results.hidden=true;check.disabled=false;
  status.textContent="未照合";
}
function pcm(buffer){
  const v=new DataView(buffer), size=v.byteLength;
  const tag=(p)=>String.fromCharCode(...new Uint8Array(buffer,p,4));
  if(size<44||tag(0)!=="RIFF"||tag(8)!=="WAVE"||v.getUint32(4,true)+8!==size)invalid("WAV形式不正");
  let fmt=null,data=null;
  for(let p=12;p<size;){
    if(p+8>size)invalid("WAVチャンク不正");
    const type=tag(p),n=v.getUint32(p+4,true),start=p+8,end=start+n;
    if(end+(n%2)>size)invalid("WAVチャンク欠損");
    if(type==="fmt "){
      if(fmt||n<16)invalid("WAV fmt不正");
      fmt={format:v.getUint16(start,true),channels:v.getUint16(start+2,true),sample_rate:v.getUint32(start+4,true),byteRate:v.getUint32(start+8,true),align:v.getUint16(start+12,true),bits:v.getUint16(start+14,true)};
    }else if(type==="data"){
      if(data)invalid("重複dataチャンク");
      data={start,end,n};
    }
    p=end+(n%2);
  }
  if(!fmt||!data||fmt.format!==1||![1,2].includes(fmt.channels)||fmt.sample_rate!==48000||fmt.bits!==16||fmt.align!==2*fmt.channels||fmt.byteRate!==48000*fmt.align||data.n%fmt.align!==0)invalid("PCM16 / 48kHz / mono・stereo が必要");
  const frames=data.n/fmt.align;
  if(frames<1||frames>48000*120)invalid("音声の長さは120秒以内");
  let peak=0,energy=0,clips=0;
  for(let p=data.start;p<data.end;p+=2){const x=v.getInt16(p,true);peak=Math.max(peak,Math.abs(x));energy+=x*x;clips+=Number(x===32767||x===-32768);}
  const db=x=>x?20*Math.log10(x/32768):null;
  return {channels:fmt.channels,sample_rate:fmt.sample_rate,frames,sample_peak_dbfs:db(peak),rms_dbfs:db(Math.sqrt(energy/(data.n/2))),full_scale_samples:clips};
}
function matchMetrics(actual,record){
  if(!record||typeof record!=="object")invalid("測定記録なし");
  for(const k of ["channels","sample_rate","frames","full_scale_samples"])if(actual[k]!==record[k])invalid("測定記録不一致: "+k);
  for(const k of ["sample_peak_dbfs","rms_dbfs"]){
    if(actual[k]===null?record[k]!==null:!Number.isFinite(record[k])||Math.abs(actual[k]-record[k])>0.005)invalid("測定記録不一致: "+k);
  }
}
const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
function metrics(m){
  const db=x=>x===null?"無音":x.toFixed(2)+" dBFS";
  return (m.frames/m.sample_rate).toFixed(3)+" 秒 / "+m.channels+"ch / 48kHz｜Peak "+db(m.sample_peak_dbfs)+"｜RMS "+db(m.rms_dbfs)+"｜フルスケール "+m.full_scale_samples;
}
for(const input of inputs)input.addEventListener("change",reset);
clear.addEventListener("click",()=>{reset();for(const input of inputs)input.value="";});
check.addEventListener("click",async()=>{
  reset();const token=generation;check.disabled=true;status.textContent="端末内で照合中";
  try{
    const [a,b,r]=inputs.map(i=>i.files[0]);
    if(!a||!b||!r)invalid("3ファイルを選択してください");
    if([a,b].some(f=>f.size<44||f.size>24*1024**2)||r.size<2||r.size>64*1024)invalid("ファイルサイズ上限を超えています");
    if(!globalThis.crypto?.subtle)invalid("HTTPSまたはlocalhostで開いてください");
    const receipt=JSON.parse(await r.text());
    if(receipt.schema!=="two.audio.candidate.v1"||receipt.candidate_only!==true||!hex.test(receipt.source_sha256)||!hex.test(receipt.output_sha256)||typeof receipt.preset!=="string"||receipt.preset.length>80||typeof receipt.backend!=="string"||receipt.backend.length>300)invalid("候補receipt形式不正");
    const [ab,bb]=await Promise.all([a.arrayBuffer(),b.arrayBuffer()]);
    const [ah,bh]=await Promise.all([hash(ab),hash(bb)]);
    if(ah!==receipt.source_sha256||bh!==receipt.output_sha256)invalid("SHA-256不一致");
    const am=pcm(ab),bm=pcm(bb);
    matchMetrics(am,receipt.before);matchMetrics(bm,receipt.after);
    if(am.channels!==bm.channels||am.frames!==bm.frames||am.sample_peak_dbfs===null||bm.sample_peak_dbfs===null||bm.sample_peak_dbfs> -1||bm.full_scale_samples!==0)invalid("候補の基本QA不一致");
    if(token!==generation)return;
    urls=[ab,bb].map(x=>URL.createObjectURL(new Blob([x],{type:"audio/wav"})));
    players.forEach((p,i)=>{p.src=urls[i];});
    get("audio-meta").textContent="未採用候補｜"+receipt.preset+"｜"+receipt.backend;
    get("audio-a-metrics").textContent=metrics(am);get("audio-b-metrics").textContent=metrics(bm);
    results.hidden=false;status.textContent="照合 PASS：原本・候補 SHA 2/2、PCM測定一致（端末内）";
  }catch(e){if(token===generation){status.textContent="照合失敗："+(e instanceof Error?e.message:"不明なエラー");results.hidden=true;}}
  finally{if(token===generation)check.disabled=false;}
});
players.forEach((p,i)=>p.addEventListener("play",()=>{last=i;players[1-i].pause();}));
get("audio-switch").addEventListener("click",()=>{
  if(results.hidden)return;
  const prev=players[last],next=players[1-last],position=prev.currentTime;
  if(next.readyState<1||!Number.isFinite(next.duration)){status.textContent="音声の読み込み完了を待ってください";return;}
  prev.pause();next.currentTime=Math.min(position,next.duration);next.play().catch(()=>{status.textContent="再生できません。音声の再生ボタンを押してください";});
});
window.addEventListener("pagehide",reset);
})();