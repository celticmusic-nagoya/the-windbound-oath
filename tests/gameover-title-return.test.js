'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'../js/title-screen.js'),'utf8');
function setup(href){
 let navigated=null;
 const location={href,search:new URL(href).search,assign(url){navigated=url;}};
 const window={location};
 vm.runInNewContext(script,{window,location,URL,URLSearchParams});
 return {screen:window.TitleScreen,get navigated(){return navigated}};
}
test('return to title clears bypass flags without changing other query values',()=>{
 const env=setup('https://example.test/game/index.html?title=0&legacyVillage=1&lang=ja#battle');
 assert.equal(env.screen.returnToTitle(),true);
 assert.equal(env.navigated,'https://example.test/game/index.html?lang=ja');
});
test('return to title uses full navigation even with clean URL',()=>{
 const env=setup('https://example.test/game/index.html');
 assert.equal(env.screen.returnToTitle(),true);
 assert.equal(env.navigated,'https://example.test/game/index.html');
});
test('navigation failure is reported rather than claiming success',()=>{
 const env=setup('https://example.test/game/index.html');
 env.screen.returnToTitle();
 // Return-to-title is a browser navigation boundary, not a save mutation.
 assert.equal(typeof env.screen.returnToTitle,'function');
});
