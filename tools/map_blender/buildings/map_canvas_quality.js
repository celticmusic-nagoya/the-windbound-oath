/* MAP-GFX-03: opt-in canvas renderer bridge, not connected to legacy DOM field. */
(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 else root.TWOMapCanvasQuality=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 function configure(canvas,cssWidth,cssHeight,dpr,config,policy){
  if(!canvas||typeof canvas.getContext!=="function")throw Error("canvas required");
  const size=policy.canvasSize(cssWidth,cssHeight,dpr,config);
  const ctx=canvas.getContext("2d");
  if(!ctx)throw Error("2d context unavailable");
  if(canvas.width!==size.width)canvas.width=size.width;
  if(canvas.height!==size.height)canvas.height=size.height;
  canvas.style.width=cssWidth+"px";canvas.style.height=cssHeight+"px";
  // World units stay in CSS pixels. UI should be rendered separately at native resolution.
  const sx=size.width/cssWidth,sy=size.height/cssHeight;
  ctx.setTransform(sx,0,0,sy,0,0);
  return {ctx,width:size.width,height:size.height,scaleX:sx,scaleY:sy};
 }
 function shouldRender(instance,config,policy,seed=0){
  if(!instance||!instance.id)throw Error("instance id required");
  if(instance.interactive||instance.questCritical||instance.eventCritical||instance.collision==="interactive")return true;
  if(instance.category!=="decorative_vegetation")return true;
  return policy.visibleDecoration(instance.id,seed,config.vegetationDensity);
 }
 return Object.freeze({configure,shouldRender});
});
