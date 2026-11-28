// V82 candidate: pure altar VFX controller, no game integration.
// Input is explicit scene time in milliseconds. All coordinates are provisional local effect offsets.
// y is visual up; engine adapter must map to verified scene transform. Base model is never modified.
// Renderer must clone per-instance materials and apply visibility/emission; no automatic scene trigger.
export function createAltarVfx({reducedMotion=false,particleCount=24}={}) {
  if(!Number.isInteger(particleCount)||particleCount<0||particleCount>24)throw new RangeError("particle budget 0..24");
  const clamp=x=>Math.max(0,Math.min(1,x));
  const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
  const stages=[["01_stele",0,650],["02_posts",550,850],["03_floor",1150,1100]];
  let generation=0,start=null,last=null,stop=null;
  const time=t=>{if(!Number.isFinite(t)||t<0)throw new RangeError("finite nonnegative monotonic milliseconds");if(last!==null&&t<last)throw new RangeError("clock went backwards");last=t;return t;};
  const dormant=()=>({phase:"dormant",layers:stages.map(([id])=>({id,visible:false,emission:0})),floating:{visible:false,y:0,opacity:0},particles:[]});
  function sample(t){
    time(t);
    if(start===null)return dormant();
    const elapsed=t-start;
    const fade=stop===null?1:1-smooth((t-stop)/750);
    if(fade<=0){start=null;stop=null;return dormant();}
    const layers=stages.map(([id,offset,duration])=>{let a=(reducedMotion?(elapsed>=offset?1:0):smooth((elapsed-offset)/duration))*fade;return {id,visible:a>0,emission:a};});
    const a=reducedMotion?0:smooth((elapsed-1800)/1000)*fade;
    const floating={visible:a>0,y:0.65*a,opacity:a};
    const particles=[];
    if(a>0)for(let i=0;i<particleCount;i++){
      const angle=i*2.399963229728653;
      const f=((elapsed-1800)/2400+i*0.61803398875)%1;
      const radius=0.36+0.74*((i*37%101)/100);
      particles.push({id:i,x:radius*Math.cos(angle+f*.45),y:0.12+1.7*f,z:radius*Math.sin(angle+f*.45),opacity:a*Math.sin(Math.PI*f)**2});
    }
    return {phase:stop!==null?"fading":elapsed<2250?"awakening":"active",layers,floating,particles};
  }
  return Object.freeze({
    activate(t){time(t);generation++;start=t;stop=null;return generation;},
    sample(t){return sample(t);},
    fadeOut(token,t){if(token!==generation||start===null)return false;time(t);if(stop===null)stop=t;return true;},
    reset(){generation++;start=null;stop=null;last=null;return dormant();},
    get generation(){return generation;}
  });
}
