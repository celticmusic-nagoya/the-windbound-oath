// V88 candidate: measured local pivot, camera-facing basis and continuous tile weights.
// GLTF Y-up, azimuth zero +X, positive azimuth toward -Z.
// Input direction is object-to-camera in original oak local frame, not world coordinates.
const PIVOT=Object.freeze([0.033129096031188965,2.4933953285217285,-0.17469823360443115]);
const SPAN=8.853480603434726, rad=Math.PI/180;
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const unit=v=>{const l=Math.hypot(...v);if(!(l>1e-9))throw new RangeError('zero direction');return v.map(x=>x/l)};
export function selectOak({direction,spanPx,previous='mesh'}){
  if(!Array.isArray(direction)||direction.length!==3||!direction.every(Number.isFinite)||!Number.isFinite(spanPx)||spanPx<0||!['mesh','impostor'].includes(previous))throw new TypeError('invalid oak input');
  const d=unit(direction), rawElev=Math.asin(Math.max(-1,Math.min(1,d[1])))/rad;
  const limit=previous==='impostor'?12:10; // measured 12px ceiling, conservative 10px entry
  if(spanPx>limit||Math.abs(rawElev)>35+1e-9)return {mode:'mesh'};
  const elev=Math.max(-35,Math.min(35,rawElev));
  const az=((Math.atan2(-d[2],d[0])/rad)%360+360)%360;
  const right=unit(cross([0,1,0],d)),up=unit(cross(d,right));
  const a=az/45, a0=Math.floor(a), a1=(a0+1)%8, t=a-a0;
  const e=(elev+35)/35,e0=Math.min(1,Math.floor(e)),e1=e0+1,s=e-e0;
  const weights=[[a0,e0,(1-t)*(1-s)],[a1,e0,t*(1-s)],[a0,e1,(1-t)*s],[a1,e1,t*s]]
      .filter(v=>v[2]>1e-10).map(([col,row,weight])=>({index:row*8+col,col,row,weight,
      uv:[(col*256+.5)/2048,(row*256+.5)/1024,((col+1)*256-.5)/2048,((row+1)*256-.5)/1024]}));
  // corners in local coordinates (GLTF texture top-left): LL, LR, UR, UL
  const corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,y])=>PIVOT.map((v,i)=>v+SPAN*.5*(x*right[i]+y*up[i])));
  return {mode:'impostor',azimuth:az,elevation:elev,right,up,normal:d,corners,weights};
}
// For software reference / shader implementation: combine linear RGB with alpha-premultiplied weights.
export function mixOak(samples,weights){
  if(samples.length!==weights.length||!samples.length||!weights.every(w=>Number.isFinite(w)&&w>=0)||Math.abs(weights.reduce((a,b)=>a+b,0)-1)>1e-7||samples.some(v=>v.length!==4||!v.every(x=>Number.isFinite(x)&&x>=0&&x<=1)))throw new TypeError('invalid samples');
  const a=samples.reduce((s,v,i)=>s+v[3]*weights[i],0);
  if(a<1e-9)return [0,0,0,0];
  return [0,1,2].map(k=>samples.reduce((s,v,i)=>s+v[k]*v[3]*weights[i],0)/a).concat(a);
}
