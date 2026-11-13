/* MAP-GFX-05: candidate SETTINGS integration. Does not change camera/DOM layout. */
(function(root){
 "use strict";
 const settings=root.TWOMapGraphicsSettings,dom=root.TWOMapDomQuality;
 if(!settings||!dom||!root.TWOMapGraphicsPolicy)return;
 let controller;
 try{
  controller=settings.create(root.localStorage,function(config){
   if(root.document&&root.document.body)dom.apply(root.document.body,config);
   root.dispatchEvent(new CustomEvent("two:graphics-quality-change",{detail:{...config}}));
  });
  controller.read();
 }catch(e){return;}
 root.TWOMapGraphicsController=controller;
 root.TWOMapGraphicsMount=function(container){
  if(!container)return null;
  return settings.mount(container,controller,root.document);
 };
})(window);
