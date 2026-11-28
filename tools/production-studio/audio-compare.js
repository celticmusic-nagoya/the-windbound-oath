(() => {
"use strict";
const get=id=>document.getElementById(id);
const inputs=["audio-source","audio-candidate","audio-receipt"].map(get);
const players=["audio-a","audio-b"].map(get);
const check=get("audio-check"), clear=get("audio-clear"), status=get("audio-status"), results=get("audio-results");
const loudInput=get("audio-loudness"),level=get("audio-match-level"),loudResults=get("audio-loudness-results"),loudStatus=get("audio-loudness-status"),gainStatus=get("audio-gain-status");
const mode=get("audio-mode"), musicInputs=[get("audio-music-a"),get("audio-music-b")], allInputs=[...inputs,loudInput,...musicInputs];
const MUSIC=[
 {name:"A01",archiveBytes:412600,archiveSha:"6c2125a6cdc89c73f249786f6e83aea3d6da26fdab716185fc59bd1129476e62",bytes:408435,sha:"00ffc1e7c44bb5b44549a1464f170965985a082229820cca3eefc483ef8f3136",integrated_lufs:-17.02,true_peak_dbtp:-8.57,loudness_range_lu:1.4},
 {name:"A02",archiveBytes:360993,archiveSha:"98037f0f425e478fbaba510da1e044ef685e4a593dabb60b7432323bb1043288",bytes:356433,sha:"41769209ea7e6fd679c6c117de0834fc09d397c3cc991ec6bceb4cbc1e62bf52",integrated_lufs:-17.20,true_peak_dbtp:-9.06,loudness_range_lu:1.3}
];
let generation=0, urls=[], last=0, gains=null, audioContext=null, gainNodes=null;
const hex=/^[a-f0-9]{64}$/;
function invalid(message){throw new Error(message);}
function reset(){
  generation++;
  gains=null;level.checked=false;level.disabled=true;loudResults.hidden=true;loudStatus.textContent="追加測定記録なし";gainStatus.textContent="補正なし";
  if(gainNodes)for(const n of gainNodes)n.gain.value=1;
  for(const a of players){a.pause();a.loop=false;a.removeAttribute("src");a.load();}
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
for(const input of allInputs)input.addEventListener("change",reset);
function setMode(){reset();const music=mode.value==="music";get("audio-wav-inputs").hidden=music;get("audio-music-inputs").hidden=!music;get("audio-a-title").textContent=music?"A｜A01":"A｜原本";get("audio-b-title").textContent=music?"B｜A02":"B｜加工候補";}
mode.addEventListener("change",()=>{for(const input of allInputs)input.value="";setMode();});
clear.addEventListener("click",()=>{reset();for(const input of allInputs)input.value="";});
setMode();
// Only the exact reviewed archive is eligible for extraction. No general ZIP upload or filesystem writes.
async function pinnedOpus(file,pin){
  if(!file||![pin.bytes,pin.archiveBytes].includes(file.size))invalid(pin.name+" ファイルサイズ不一致");
  const b=await file.arrayBuffer(), digest=await hash(b);
  let data=b;
  if(digest===pin.archiveSha&&file.size===pin.archiveBytes){
    const v=new DataView(b),size=v.byteLength;
    let e=size-22;
    while(e>=Math.max(0,size-65557)){if(v.getUint32(e,true)===0x06054b50&&e+22+v.getUint16(e+20,true)===size)break;e--;}
    if(e<Math.max(0,size-65557))invalid("ZIP終端不正");
    const count=v.getUint16(e+10,true),start=v.getUint32(e+16,true),end=start+v.getUint32(e+12,true);
    if(v.getUint16(e+4,true)||v.getUint16(e+6,true)||count!==v.getUint16(e+8,true)||count<1||count>16||end>e)invalid("ZIP中央ディレクトリ不正");
    let p=start,found=null;
    for(let i=0;i<count;i++){
      if(p+46>end||v.getUint32(p,true)!==0x02014b50)invalid("ZIP項目不正");
      const flags=v.getUint16(p+8,true),method=v.getUint16(p+10,true),crc=v.getUint32(p+16,true),packed=v.getUint32(p+20,true),n=v.getUint32(p+24,true),nl=v.getUint16(p+28,true),next=p+46+nl+v.getUint16(p+30,true)+v.getUint16(p+32,true),off=v.getUint32(p+42,true);
      if(next>end)invalid("ZIP項目範囲不正");
      const name=new TextDecoder().decode(new Uint8Array(b,p+46,nl));p=next;
      if(name!=="delivery.ogg")continue;
      if(found||flags&1||![0,8].includes(method)||n!==pin.bytes||packed>pin.archiveBytes||off+30>start||v.getUint32(off,true)!==0x04034b50||v.getUint16(off+8,true)!==method)invalid("ZIP音声項目不正");
      const pos=off+30+v.getUint16(off+26,true)+v.getUint16(off+28,true);
      if(pos+packed>start||method===0&&packed!==n)invalid("ZIP音声範囲不正");
      const bytes=new Uint8Array(b,pos,packed);
      const blob=method===0?new Blob([bytes]):await inflateBounded(bytes,n);
      const unpacked=await blob.arrayBuffer();
      if(unpacked.byteLength!==n||crc32(new Uint8Array(unpacked))!==crc)invalid("ZIP音声CRC不一致");
      found=unpacked;
    }
    if(p!==end||!found)invalid("ZIP音声項目なし");
    data=found;
  }else if(digest!==pin.sha||file.size!==pin.bytes)invalid(pin.name+" SHA-256不一致");
  if(data.byteLength!==pin.bytes||await hash(data)!==pin.sha||new TextDecoder().decode(new Uint8Array(data,0,4))!=="OggS")invalid(pin.name+" Ogg SHA-256不一致");
  return data;
}
async function compareMusic(token){
  const buffers=await Promise.all(musicInputs.map((input,i)=>pinnedOpus(input.files[0],MUSIC[i])));
  if(token!==generation)return;
  urls=buffers.map(x=>URL.createObjectURL(new Blob([x],{type:"audio/ogg; codecs=opus"})));
  players.forEach((p,i)=>{p.loop=true;p.src=urls[i];});
  get("audio-meta").textContent="リルド村・昼｜A01 / A02｜未採用候補";
  for(let i=0;i<2;i++)get(i?"audio-b-metrics":"audio-a-metrics").textContent="24.000 秒 / 2ch / 48kHz｜Ogg Opus "+MUSIC[i].bytes.toLocaleString("ja-JP")+" B";
  showLoudness({before:MUSIC[0],after:MUSIC[1],delta_lufs:MUSIC[1].integrated_lufs-MUSIC[0].integrated_lufs});
  loudStatus.textContent="既知成果物のSHA一致。表示は検証済みActions測定値（再測定なし）。";
  results.hidden=false;status.textContent="照合 PASS：A01・A02 Opus SHA 2/2（端末内）";
}
check.addEventListener("click",async()=>{
  reset();const token=generation;check.disabled=true;status.textContent="端末内で照合中";
  try{
    if(mode.value==="music"){if(!globalThis.crypto?.subtle)invalid("HTTPSまたはlocalhostで開いてください");await compareMusic(token);return;}
    const [a,b,r]=inputs.map(i=>i.files[0]);
    if(!a||!b||!r)invalid("3ファイルを選択してください");
    if([a,b].some(f=>f.size<44||f.size>24*1024**2)||r.size<2||r.size>64*1024)invalid("ファイルサイズ上限を超えています");
    if(!globalThis.crypto?.subtle)invalid("HTTPSまたはlocalhostで開いてください");
    const receiptBytes=await r.arrayBuffer();
    const receipt=JSON.parse(new TextDecoder().decode(receiptBytes));
    if(receipt.schema!=="two.audio.candidate.v1"||receipt.candidate_only!==true||!hex.test(receipt.source_sha256)||!hex.test(receipt.output_sha256)||typeof receipt.preset!=="string"||receipt.preset.length>80||typeof receipt.backend!=="string"||receipt.backend.length>300)invalid("候補receipt形式不正");
    const [ab,bb]=await Promise.all([a.arrayBuffer(),b.arrayBuffer()]);
    const [ah,bh]=await Promise.all([hash(ab),hash(bb)]);
    if(ah!==receipt.source_sha256||bh!==receipt.output_sha256)invalid("SHA-256不一致");
    const am=pcm(ab),bm=pcm(bb);
    matchMetrics(am,receipt.before);matchMetrics(bm,receipt.after);
    if(am.channels!==bm.channels||am.frames!==bm.frames||am.sample_peak_dbfs===null||bm.sample_peak_dbfs===null||bm.sample_peak_dbfs> -1||bm.full_scale_samples!==0)invalid("候補の基本QA不一致");
    let loud=null,loudError=null;
    if(loudInput.files[0]){
      try{
        const f=loudInput.files[0];
        if(f.size<2||f.size>128*1024)invalid("測定記録サイズ不正");
        loud=selectLoudness(JSON.parse(await f.text()),await hash(receiptBytes),ah,bh,am,bm);
      }catch(e){loudError=e instanceof Error?e.message:"不明なエラー";}
    }
    if(token!==generation)return;
    if(loud)showLoudness(loud);else if(loudError)loudStatus.textContent="追加測定記録を拒否："+loudError;
    urls=[ab,bb].map(x=>URL.createObjectURL(new Blob([x],{type:"audio/wav"})));
    players.forEach((p,i)=>{p.src=urls[i];});
    get("audio-meta").textContent="未採用候補｜"+receipt.preset+"｜"+receipt.backend;
    get("audio-a-metrics").textContent=metrics(am);get("audio-b-metrics").textContent=metrics(bm);
    results.hidden=false;status.textContent="照合 PASS：原本・候補 SHA 2/2、PCM測定一致（端末内）";
  }catch(e){if(token===generation){status.textContent="照合失敗："+(e instanceof Error?e.message:"不明なエラー");results.hidden=true;}}
  finally{if(token===generation)check.disabled=false;}
});
function selectLoudness(report,rh,ah,bh,am,bm){
  let item=report;
  if(report?.schema==="two.audio.packet-inspection.v1"){
    if(report.candidate_only!==true||!report.pairs||typeof report.pairs!=="object"||Array.isArray(report.pairs))invalid("packet形式不正");
    const rows=Object.values(report.pairs);
    if(rows.length>16)invalid("packet組数上限");
    const matched=rows.filter(x=>x?.source_receipt_sha256===rh&&x?.before?.sha256===ah&&x?.after?.sha256===bh);
    if(!matched.length)invalid("一致する測定記録なし");
    // warm and warm-repeat may be byte-identical; reject any conflicting duplicate.
    if(matched.some(x=>JSON.stringify(x)!==JSON.stringify(matched[0])))invalid("測定記録が競合");
    item=matched[0];
  }
  if(item?.schema!=="two.audio.loudness-inspection.v1"||item.candidate_only!==true||item.source_receipt_sha256!==rh||item.before?.sha256!==ah||item.after?.sha256!==bh||item.qa?.sha_pcm!=="PASS"||item.qa?.lufs!=="MEASURED"||item.qa?.true_peak!=="MEASURED")invalid("測定記録の来歴不一致");
  for(const [m,p] of [[item.before,am],[item.after,bm]]){
    matchMetrics(p,m.pcm);
    if(!Number.isFinite(m.integrated_lufs)||m.integrated_lufs< -70||m.integrated_lufs>10||!Number.isFinite(m.true_peak_dbtp)||m.true_peak_dbtp< -100||m.true_peak_dbtp>10||!Number.isFinite(m.loudness_range_lu)||m.loudness_range_lu<0||m.loudness_range_lu>100)invalid("ラウドネス値不正");
  }
  const a=item.before.integrated_lufs,b=item.after.integrated_lufs;
  if(!Number.isFinite(item.delta_lufs)||Math.abs(item.delta_lufs-(b-a))>0.011)invalid("LUFS差分不一致");
  return item;
}
function showLoudness(item){
  const a=item.before,b=item.after;
  const describe=m=>m.integrated_lufs.toFixed(2)+" LUFS / "+m.true_peak_dbtp.toFixed(2)+" dBTP / LRA "+m.loudness_range_lu.toFixed(2)+" LU";
  get("audio-loudness-a").textContent="A｜"+describe(a);
  get("audio-loudness-b").textContent="B｜"+describe(b);
  get("audio-loudness-delta").textContent="B−A： "+item.delta_lufs.toFixed(2)+" LU｜LRAは短音源での参考値";
  const target=Math.min(a.integrated_lufs,b.integrated_lufs);
  gains=[target-a.integrated_lufs,target-b.integrated_lufs];
  loudResults.hidden=false;
  level.disabled=gains.some(x=>x< -24);
  loudStatus.textContent="測定記録との紐付け一致（SHA・PCM）。発行者認証・再測定なし。";
  gainStatus.textContent=level.disabled?"音量差が24 LUを超えるため補正不可":"補正なし";
}
level.addEventListener("change",async()=>{
  const token=generation;
  if(!gains||level.disabled)return;
  try{
    if(level.checked){
      if(!audioContext){
        const AC=window.AudioContext||window.webkitAudioContext;
        if(!AC)invalid("Web Audio未対応");
        audioContext=new AC();
        gainNodes=players.map(p=>{const source=audioContext.createMediaElementSource(p),g=audioContext.createGain();source.connect(g);g.connect(audioContext.destination);return g;});
      }
      await audioContext.resume();
      if(token!==generation||!level.checked)return;
      if(audioContext.state!=="running")invalid("AudioContextを開始できません");
      gains.forEach((db,i)=>{gainNodes[i].gain.value=Math.pow(10,db/20);});
      gainStatus.textContent="試聴補正 A "+gains[0].toFixed(2)+" dB / B "+gains[1].toFixed(2)+" dB（減衰のみ）";
    }else{
      if(gainNodes)for(const n of gainNodes)n.gain.value=1;
      gainStatus.textContent="補正なし";
    }
  }catch(e){if(token===generation){level.checked=false;if(gainNodes)for(const n of gainNodes)n.gain.value=1;gainStatus.textContent="補正不可："+e.message;}}
});
players.forEach((p,i)=>p.addEventListener("play",()=>{last=i;players[1-i].pause();if(audioContext&&audioContext.state!=="running")audioContext.resume().catch(()=>{gainStatus.textContent="音声再生の再操作が必要";});}));
get("audio-switch").addEventListener("click",()=>{
  if(results.hidden)return;
  const prev=players[last],next=players[1-last],position=prev.currentTime;
  if(next.readyState<1||!Number.isFinite(next.duration)){status.textContent="音声の読み込み完了を待ってください";return;}
  prev.pause();next.currentTime=Math.min(position,next.duration);next.play().catch(()=>{status.textContent="再生できません。音声の再生ボタンを押してください";});
});
window.addEventListener("pagehide",reset);
})();