// Shared image readiness. A successful request is not ready until decode succeeds.
(() => {
 'use strict';
 const pool=new Map();
 function decode(image,timeoutMs=10000){
  return new Promise(resolve=>{
   let finished=false,fetched=Boolean(image.complete&&image.naturalWidth),timer;
   const end=(status,error)=>{if(finished)return;finished=true;clearTimeout(timer);image.removeEventListener('load',loaded);image.removeEventListener('error',failed);resolve({status,fetched,decoded:status==='ready',image,error});};
   const failed=()=>end('failed','fetch');
   const loaded=()=>{if(finished)return;fetched=true;Promise.resolve().then(()=>image.decode()).then(()=>image.naturalWidth?end('ready'):end('failed','decode'),()=>end('failed','decode'));};
   timer=setTimeout(()=>end('timeout',fetched?'decode':'fetch'),timeoutMs);
   image.addEventListener('load',loaded);image.addEventListener('error',failed);
   if(image.complete){if(image.naturalWidth)loaded();else if(image.getAttribute('src'))failed();}
  });
 }
 function image(url,opt={}){
  const key=new URL(url,document.baseURI).href;
  let record=pool.get(key);
  if(record&&(record.status==='pending'||record.status==='ready'))return record.promise;
  const im=new Image();im.decoding='async';record={status:'pending',image:im};pool.set(key,record);
  record.promise=decode(im,opt.timeoutMs).then(result=>{record.status=result.status;return result;});
  im.src=key;return record.promise;
 }
 window.LoadingAssets=Object.freeze({decode,image});
})();
