import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const {chromium}=createRequire(new URL('../production-studio/package.json',import.meta.url))('playwright');
const root=resolve(process.argv[2]);
const browser=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
try{
 const page=await browser.newPage({viewport:{width:390,height:844}});
 await page.goto('about:blank');
 const results={};
 for(const role of ['loop','oneshot']){
  const receipt=JSON.parse(await readFile(join(root,role,'delivery.json'),'utf8'));
  for(const [format,meta] of Object.entries(receipt.formats)){
   const bytes=await readFile(join(root,role,meta.file));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),meta.sha256);
   // Verify one-shot fallback and actual Opus loop. MP3 loop is deliberately not qualified.
   if(role==='loop'&&format==='mp3')continue;
   const result=await page.evaluate(async ({data,format,role,frames,channels})=>{
     const raw=Uint8Array.from(atob(data),c=>c.charCodeAt(0));
     const ctx=new OfflineAudioContext(channels,frames*2,48000);
     const buf=await ctx.decodeAudioData(raw.buffer.slice(0));
     const src=ctx.createBufferSource();src.buffer=buf;src.loop=role==='loop';
     src.connect(ctx.destination);src.start();
     const rendered=await ctx.startRendering();
     let peak=0,jump=0,slope=0,repeat=0;
     for(let c=0;c<channels;c++){
      const x=rendered.getChannelData(c);
      for(let i=0;i<x.length;i++)peak=Math.max(peak,Math.abs(x[i]));
      if(role==='loop'){
       jump=Math.max(jump,Math.abs(x[frames]-x[frames-1]));
       slope=Math.max(slope,Math.abs((x[frames+1]-x[frames])-(x[frames-1]-x[frames-2])));
       for(let i=0;i<frames;i++)repeat=Math.max(repeat,Math.abs(x[i]-x[i+frames]));
      }
     }
     const url=URL.createObjectURL(new Blob([raw],{type:format==='opus'?'audio/ogg':'audio/mpeg'}));
     const player=new Audio();player.src=url;
     try{
      await player.play();
      await new Promise((resolve,reject)=>{const end=Date.now()+3000;const tick=()=>player.currentTime>0.02?resolve():Date.now()>end?reject(Error('playback did not advance')):setTimeout(tick,25);tick();});
      return {frames:buf.length,channels:buf.numberOfChannels,sampleRate:buf.sampleRate,peak,jump,slope,repeat,playback:true};
     }finally{player.pause();player.removeAttribute('src');player.load();URL.revokeObjectURL(url);}
   },{data:bytes.toString('base64'),format,role,frames:receipt.source_pcm.frames,channels:receipt.source_pcm.channels});
   assert.equal(result.channels,receipt.source_pcm.channels);assert.equal(result.sampleRate,48000);assert.ok(result.peak>0&&result.peak<1);
   assert.ok(result.playback);
   if(role==='loop'){
    assert.equal(result.frames,receipt.source_pcm.frames);
    assert.ok(result.jump<=receipt.thresholds.sample_jump_fs&&result.slope<=receipt.thresholds.slope_difference_fs);
    assert.ok(result.repeat<1e-6,'two rendered cycles differ');
   }else assert.ok(Math.abs(result.frames-receipt.source_pcm.frames)<=960);
   results[role+'-'+format]=result;
  }
 }
 await writeFile(join(root,'browser-delivery-qa.json'),JSON.stringify({results,scope:'Chromium decode, actual playback and offline two-cycle render; not Android or listening/game adoption'},null,2)+'\n',{flag:'wx'});
 console.log('PASS: browser delivery',JSON.stringify(results));
}finally{await browser.close();}
