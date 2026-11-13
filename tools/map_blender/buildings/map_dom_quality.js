/* MAP-GFX-04: reversible DOM rendering quality adapter.
 * No camera/world transforms or interaction geometry are changed. */
(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 else root.TWOMapDomQuality=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 const VARS=["--two-map-effect-opacity","--two-map-shadow-opacity","--two-map-decorative-density"];
 function apply(rootElement,config){
  if(!rootElement||!rootElement.style||!rootElement.dataset)throw Error("root element required");
  if(!config||!["ultra","high","standard","low"].includes(config.preset))throw Error("invalid graphics config");
  const effects={ultra:1,high:1,standard:.7,low:.3};
  const shadows={ultra:1,high:.75,standard:.35,low:0};
  rootElement.dataset.twoMapQuality=config.preset;
  rootElement.style.setProperty(VARS[0],String(effects[config.preset]));
  rootElement.style.setProperty(VARS[1],String(shadows[config.preset]));
  rootElement.style.setProperty(VARS[2],String(config.vegetationDensity));
  return config.preset;
 }
 function clear(rootElement){
  if(!rootElement||!rootElement.style||!rootElement.dataset)throw Error("root element required");
  delete rootElement.dataset.twoMapQuality;
  for(const name of VARS)rootElement.style.removeProperty(name);
 }
 return Object.freeze({apply,clear});
});
