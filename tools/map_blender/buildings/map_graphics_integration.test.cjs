const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const base=__dirname;
const html=fs.readFileSync(path.join(base,"../../../index.html"),"utf8");
for(const name of ["map_graphics_policy.js","map_graphics_settings.js","map_dom_quality.js","map_graphics_integration.js"])
 assert.ok(html.includes("tools/map_blender/buildings/"+name),"missing script "+name);
assert.ok(html.includes("window.TWOMapGraphicsMount(body)"));
const values=new Map(),saved=new Map(),events=[];
const document={body:{dataset:{},style:{setProperty:(k,v)=>values.set(k,v),removeProperty:k=>values.delete(k)}}};
const window={document,localStorage:{getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)},dispatchEvent:e=>events.push(e)};
const context={window,CustomEvent:class{constructor(type,opts){this.type=type;this.detail=opts.detail;}},console};
context.window=context;
context.document=document;
context.localStorage=window.localStorage;
context.dispatchEvent=window.dispatchEvent;
vm.createContext(context);
for(const name of ["map_graphics_policy.js","map_graphics_settings.js","map_dom_quality.js","map_graphics_integration.js"])
 vm.runInContext(fs.readFileSync(path.join(base,name),"utf8"),context,{filename:name});
assert.equal(context.TWOMapGraphicsController.get().preset,"high");
context.TWOMapGraphicsController.set("low");
assert.equal(document.body.dataset.twoMapQuality,"low");
assert.equal(saved.has("two.map.graphics.v1"),true);
assert.equal(events.at(-1).type,"two:graphics-quality-change");
console.log("MAP-GFX-05 PASS");
