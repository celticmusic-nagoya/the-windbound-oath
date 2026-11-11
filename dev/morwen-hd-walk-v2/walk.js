/* DEV-only. No production imports. Missing art must remain NOT_READY. */
(async () => {
'use strict';
const ROOT='../../';
const $=id=>document.getElementById(id);
const status=$('status'),sprite=$('sprite'),stage=$('stage'),play=$('play'),step=$('step');
let frames=[],index=0,running=false,clock=0,last=0;
const setStatus=(msg,warn=false)=>{status.textContent=msg;status.classList.toggle('warn',warn)};
try {
 const [manifestResponse,registryResponse]=await Promise.all([
  fetch(ROOT+'data/sprite-rig/morwen_hd_left_walk6_delivery.json',{cache:'no-store'}),
  fetch(ROOT+'data/morwen-hd-canonical-v2.json',{cache:'no-store'})
 ]);
 if(!manifestResponse.ok||!registryResponse.ok)throw Error('設定ファイルのHTTP読み込みに失敗');
 const [manifest,registry]=await Promise.all([manifestResponse.json(),registryResponse.json()]);
 if(manifest.source_sha256!==registry.assets['pixel.left'].sha256)throw Error('正本SHAが一致しません');
 if(manifest.frames.length!==6||manifest.frame_size.join('x')!=='1200x1600')throw Error('フレーム仕様が不正です');
 const results=await Promise.all(manifest.frames.map(async frame=>{
  if(!/^[0-9a-f]{64}$/.test(frame.sha256||''))return {ok:false,id:frame.id,reason:'SHA未登録'};
  const img=new Image();
  img.src=ROOT+frame.path;
  try {await img.decode()}catch{return {ok:false,id:frame.id,reason:'画像なし'}};
  if(img.naturalWidth!==1200||img.naturalHeight!==1600)return {ok:false,id:frame.id,reason:'画像サイズ不一致'};
  return {ok:true,id:frame.id,src:img.src};
 }));
 const invalid=results.filter(r=>!r.ok);
 if(invalid.length){setStatus('NOT_READY: '+invalid.length+'/6 コマ未準備\n'+invalid.map(r=>r.id+': '+r.reason).join('\n'),true);return}
 frames=results.map(r=>r.src);
 function render(){
  const height=Number($('height').value),scale=height/1600;
  sprite.style.width=1200*scale+'px';sprite.style.height=height+'px';
  sprite.style.left='calc(50% - '+600*scale+'px)';
  sprite.style.top=(stage.clientHeight-36-1540*scale)+'px';
  sprite.src=frames[index];sprite.hidden=false;
  setStatus('DEVプレビュー / F'+(index+1)+' / '+$('speed').value+'fps / 実機QA未実施');
 }
 function loop(t){
  if(!running)return;
  if(!last)last=t;
  clock+=Math.min(t-last,250);last=t;
  const interval=1000/Number($('speed').value);
  if(clock>=interval){index=(index+Math.floor(clock/interval))%6;clock%=interval;render()}
  requestAnimationFrame(loop);
 }
 play.disabled=false;step.disabled=false;
 play.addEventListener('click',()=>{
  running=!running;play.textContent=running?'停止':'再生';
  if(running){last=0;clock=0;requestAnimationFrame(loop)}
 });
 step.addEventListener('click',()=>{running=false;play.textContent='再生';index=(index+1)%6;render()});
 $('height').addEventListener('change',render);
 render();
}catch(err){setStatus('FAIL: '+err.message,true)}
})();
