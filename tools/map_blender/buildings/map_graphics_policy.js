/* MAP-GFX-01: opt-in rendering policy. No game runtime wiring. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports) module.exports=api;
  else root.TWOMapGraphicsPolicy=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const PRESETS=Object.freeze({
    ultra:Object.freeze({renderScale:1,vegetationDensity:1,shadows:"high",effects:"full",targetFps:60}),
    high:Object.freeze({renderScale:.85,vegetationDensity:.85,shadows:"medium",effects:"normal",targetFps:60}),
    standard:Object.freeze({renderScale:.7,vegetationDensity:.65,shadows:"low",effects:"reduced",targetFps:60}),
    low:Object.freeze({renderScale:.5,vegetationDensity:.4,shadows:"off",effects:"minimal",targetFps:30})
  });
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  function resolve(preset="high",overrides={}){
    if(!Object.prototype.hasOwnProperty.call(PRESETS,preset))throw Error("Unknown preset: "+preset);
    const p=PRESETS[preset];
    const scale=overrides.renderScale===undefined?p.renderScale:Number(overrides.renderScale);
    if(!Number.isFinite(scale))throw Error("renderScale must be finite");
    return Object.freeze({...p,renderScale:clamp(scale,.5,1),preset});
  }
  function canvasSize(cssWidth,cssHeight,dpr,config){
    for(const n of [cssWidth,cssHeight,dpr])if(!Number.isFinite(n)||n<=0)throw Error("Invalid viewport");
    return {width:Math.max(1,Math.round(cssWidth*clamp(dpr,1,3)*config.renderScale)),
      height:Math.max(1,Math.round(cssHeight*clamp(dpr,1,3)*config.renderScale))};
  }
  // Stable deterministic thinning: only decorative foliage. Never hide interactables.
  function visibleDecoration(instanceId,seed,density){
    if(typeof instanceId!=="string"||!instanceId)throw Error("instanceId required");
    if(!Number.isFinite(density))throw Error("density must be finite");
    const s=instanceId+"|"+String(seed);let hash=2166136261;
    for(let i=0;i<s.length;i++){hash^=s.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return (hash>>>0)/4294967296<clamp(density,0,1);
  }
  return Object.freeze({PRESETS,resolve,canvasSize,visibleDecoration});
});
