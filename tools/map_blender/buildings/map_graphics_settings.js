/* MAP-GFX-02: isolated settings controller. Opt-in; does not modify save data. */
(function(root,factory){
 const api=factory(typeof module==="object"&&module.exports?require("./map_graphics_policy.js"):root.TWOMapGraphicsPolicy);
 if(typeof module==="object"&&module.exports)module.exports=api;
 else root.TWOMapGraphicsSettings=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(policy){
 "use strict";
 const KEY="two.map.graphics.v1";
 function create(storage,onChange){
  if(!policy)throw Error("Graphics policy unavailable");
  let config=policy.resolve("high");
  function emit(){if(typeof onChange==="function")onChange(config);return config;}
  function read(){
   try{
    const raw=storage.getItem(KEY);
    if(raw){const value=JSON.parse(raw);config=policy.resolve(value.preset,{renderScale:value.renderScale});}
   }catch(e){config=policy.resolve("high");}
   return emit();
  }
  function set(preset,renderScale){
   const next=policy.resolve(preset,renderScale===undefined?{}:{renderScale});
   storage.setItem(KEY,JSON.stringify({preset:next.preset,renderScale:next.renderScale}));
   config=next;return emit();
  }
  return Object.freeze({read,set,get:()=>config});
 }
 function mount(container,controller,doc){
  if(!container||!doc)throw Error("container and document required");
  const wrapper=doc.createElement("section");wrapper.className="charStatus";
  const heading=doc.createElement("b");heading.textContent="グラフィック（試験設定）";wrapper.appendChild(heading);
  const label=doc.createElement("label");label.textContent="画質プリセット ";wrapper.appendChild(label);
  const select=doc.createElement("select");select.setAttribute("aria-label","画質プリセット");
  for(const name of Object.keys(policy.PRESETS)){
   const option=doc.createElement("option");option.value=name;option.textContent=({ultra:"最高",high:"高",standard:"標準",low:"軽量"})[name];select.appendChild(option);
  }
  label.appendChild(select);
  const scaleLabel=doc.createElement("label");scaleLabel.textContent=" 描画解像度 ";
  const scale=doc.createElement("input");scale.type="range";scale.min="50";scale.max="100";scale.step="5";scale.setAttribute("aria-label","描画解像度");
  const output=doc.createElement("output");scaleLabel.appendChild(scale);scaleLabel.appendChild(output);wrapper.appendChild(scaleLabel);
  const help=doc.createElement("p");help.textContent="設定は保存されます。描画エンジンへの接続までは見た目は変わりません。";wrapper.appendChild(help);
  function sync(c){select.value=c.preset;scale.value=String(Math.round(c.renderScale*100));output.textContent=scale.value+"%";}
  select.addEventListener("change",()=>sync(controller.set(select.value)));
  scale.addEventListener("change",()=>sync(controller.set(select.value,Number(scale.value)/100)));
  sync(controller.get());container.appendChild(wrapper);return wrapper;
 }
 return Object.freeze({KEY,create,mount});
});
