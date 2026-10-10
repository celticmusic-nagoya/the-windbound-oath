/* Shared NPC conversation trigger (M5.5). One entry point for every way a conversation can start:
 *   FieldTalk.talk(id, {source})   - real room/village UI handlers and the DEV review interaction both call this.
 * Line providers register by NPC id (LindDialogue, ForestWarnings); the DEV review's 'lind-field-interaction'
 * CustomEvent is translated here once, so providers no longer listen for it themselves. */
(function () {
  'use strict';
  const providers=new Map();
  const history=[];
  function register(ids,lineFn){for(const id of [].concat(ids))providers.set(id,lineFn);}
  function has(id){return providers.has(id);}
  function talk(id,{source='ui'}={}){
    const provider=providers.get(id);
    if(!provider||typeof say!=='function')return false;
    const text=provider(id);if(!text)return false;
    history.push({id,source,at:Date.now()});if(history.length>20)history.shift();
    say(text);
    window.dispatchEvent(new CustomEvent('field-talk',{detail:{id,source}}));
    return true;
  }
  window.addEventListener('lind-field-interaction',e=>{
    const d=e.detail;if(d&&d.id)talk(d.id,{source:'review'});
  });
  window.FieldTalk=Object.freeze({register,has,talk,get history(){return history.slice();}});
})();
