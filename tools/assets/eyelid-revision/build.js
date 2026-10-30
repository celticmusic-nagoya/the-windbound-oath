// Mechanical eye-only asset build. Creative eyelid art comes from imagegen donors; no whole generated portrait enters runtime.
async function buildEyeRevision(input) {
 const load=u=>new Promise((r,j)=>{const im=new Image();im.onload=()=>r(im);im.onerror=j;im.src=u});
 const canvas=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c};
 const pixels=im=>{const c=canvas(im.width,im.height),x=c.getContext('2d');x.drawImage(im,0,0);return x.getImageData(0,0,c.width,c.height)};
 const raw=data=>{let v='';for(let i=0;i<data.length;i+=8192)v+=String.fromCharCode(...data.subarray(i,i+8192));return btoa(v)};
 const decode=s=>Uint8ClampedArray.from(atob(s),c=>c.charCodeAt(0));
 const lerp=(a,b,t)=>a+(b-a)*t;
 const curve=(pts,x)=>{if(x<=pts[0][0])return pts[0][1];for(let i=1;i<pts.length;i++)if(x<=pts[i][0])return lerp(pts[i-1][1],pts[i][1],(x-pts[i-1][0])/(pts[i][0]-pts[i-1][0]));return pts.at(-1)[1]};
 const smooth=(v)=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v)};
 const normal=await load(input.normal),donor=await load(input.donor);
 if(normal.width!==donor.width||normal.height!==donor.height)throw Error('Donor canvas mismatch: no implicit resize or geometric shift allowed');
 const N={data:decode(input.normalRaw)},D=pixels(donor),w=normal.width,h=normal.height;
 const states=[new Uint8ClampedArray(N.data)],patches={},masks={};
 const read=(buf,x,y,ch)=>{x=Math.max(0,Math.min(w-1,Math.round(x)));y=Math.max(0,Math.min(h-1,y));const a=Math.floor(y),b=Math.min(h-1,a+1);return lerp(buf[(a*w+x)*4+ch],buf[(b*w+x)*4+ch],y-a)};
 for(const [eye,E] of Object.entries(input.eyes)){
   const [x0,y0,x1,y1]=E.box,bw=x1-x0,bh=y1-y0;
   const pm=canvas(bw,bh),pc=pm.getContext('2d');
   for(const poly of E.protect||[]){pc.beginPath();poly.forEach(([x,y],i)=>i?pc.lineTo(x-x0,y-y0):pc.moveTo(x-x0,y-y0));pc.closePath();pc.fill();}
   const protectedPixels=pc.getImageData(0,0,bw,bh).data;
   const mask=new Float32Array(bw*bh);
   for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
      const top=curve(E.top,x),low=curve(E.lower,x),closed=curve(E.closed,x);
      const mid=(x0+x1-1)/2,half=(x1-x0)/2,tip=Math.min(E.tip,5+9*Math.pow(Math.min(1,Math.abs((x-mid)/half)),4));
      const upper=Math.min(top-tip,closed-8),bottom=Math.max(low+3,closed+7);
      const fx=smooth(Math.min(x-x0,x1-1-x)/4),fy=smooth(Math.min(y-upper,bottom-y)/3);
      const pi=((y-y0)*bw+x-x0);mask[pi]=fx*fy*(1-protectedPixels[pi*4+3]/255);
      // Remove only the two independently located OLD lash tips, not the nearby eyebrow arc.
      for(const[a,b,c,d]of E.erase_lash_islands||[]){const i=(y*w+x)*4;
        if(x>=a&&x<c&&y>=b&&y<d&&N.data[i+1]<210&&D.data[i]>200&&D.data[i+1]>125&&D.data[i+1]>N.data[i+1]+10)mask[pi]=1;
      }
   }
   masks[eye]=mask;
 }
 for(let s=1;s<=4;s++){
   const k=[0,.30,.60,.85,1][s],out=new Uint8ClampedArray(N.data);
   for(const [eye,E] of Object.entries(input.eyes)){
    const [x0,y0,x1,y1]=E.box,bw=x1-x0,bh=y1-y0,patch=new Uint8ClampedArray(bw*bh*4);
    for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
      const pi=(y-y0)*bw+x-x0,weight=masks[eye][pi],i=(y*w+x)*4,j=pi*4;
      if(!weight)continue;
      const T=curve(E.top,x),LB=curve(E.lash_bottom,x),LO=curve(E.lower,x),C=curve(E.closed,x),LC=(T+LB)/2;
      const d=k*(C-LC),thin=1-.4*k,newT=T+d,newB=newT+(LB-T)*thin;
      const lower=lerp(LO,C,k);
      for(let ch=0;ch<3;ch++){
        let v;
        if(s===4)v=D.data[i+ch];
        else if(y>=newT&&y<=newB){
          // Move original lash texture toward the approved donor curve, never rotate/scale the character.
          const sy=T+(y-newT)/thin;v=read(N.data,x,sy,ch);
        } else if(y<newT)v=read(D.data,x,Math.min(y,C-7),ch);
        else if(y>lower)v=read(D.data,x,Math.max(y,C+7),ch);
        else v=N.data[i+ch];
        out[i+ch]=Math.round(lerp(N.data[i+ch],v,weight));
      }
      // Output overlays use source-resolution coordinates and binary alpha, as in the existing shared renderer.
      const changed=[0,1,2].some(ch=>out[i+ch]!==N.data[i+ch]);
      for(let ch=0;ch<3;ch++)patch[j+ch]=out[i+ch];patch[j+3]=changed?255:0;
    }
    patches[`normal_${eye}_s${s}.png`]=raw(patch);
   }
   states.push(out);
 }
 window.eyeRevisionContext={N,w,h,states,masks,eyes:input.eyes};
 const allowedMasks={};for(const[eye,E]of Object.entries(input.eyes)){const[x0,y0,x1,y1]=E.box,m=masks[eye],a=new Uint8ClampedArray(m.length*4);for(let i=0;i<m.length;i++){a[i*4]=a[i*4+1]=a[i*4+2]=m[i]>0?255:0;a[i*4+3]=255}allowedMasks[eye]=raw(a)}
 return{patches,allowedMasks,boxes:Object.fromEntries(Object.entries(input.eyes).map(([e,v])=>[e,v.box]))};
}
function buildEyeExpression(input){
 const {N,w,h,states,masks,eyes}=window.eyeRevisionContext;
 const B=Uint8ClampedArray.from(atob(input.raw),c=>c.charCodeAt(0)),out=new Uint8ClampedArray(B),chosen=states[input.state];
 for(const[eye,E]of Object.entries(eyes)){
  const[x0,y0,x1,y1]=E.box,bw=x1-x0;
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
   const weight=masks[eye][(y-y0)*bw+x-x0],i=(y*w+x)*4;
   for(let ch=0;ch<3;ch++)out[i+ch]=Math.round(B[i+ch]*(1-weight)+chosen[i+ch]*weight);
  }
 }
 let v='';for(let i=0;i<out.length;i+=8192)v+=String.fromCharCode(...out.subarray(i,i+8192));return btoa(v);
}
