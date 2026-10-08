/* Independent training-dummy interaction object; no tutorial/battle rewrite.
 * DEV events carry reviewOnly, for safe future STEP 12 field integration. */
(function () {
  'use strict';
  let lastInteraction = null, notice = null;
  function interact(id) {
    if (!window.LindFieldReview?.active) return false;
    const object = window.LindFieldAssets.objects.find(o=>o.id===id && o.interaction);
    if (!object) return false;
    if (Math.hypot(px+17-object.x-object.width/2,py+42-object.y-object.height)>100) {
      notice.hidden=false; notice.textContent='訓練人形へ近づいてください。';
      return false;
    }
    target = null;
    lastInteraction = {id:object.id,type:object.interaction,reviewOnly:true};
    notice.hidden=false;
    notice.textContent='訓練人形 · interaction確認。剣のtutorial連携は後工程。';
    window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{...lastInteraction}}));
    return true;
  }
  function mount(parent, controls) {
    notice = document.createElement('div');notice.id='lindInteractionNotice';
    notice.hidden=true;notice.setAttribute('role','status');controls.append(notice);
    window.LindFieldAssets.objects.filter(o=>o.interaction).forEach(object=>{
      const button=document.createElement('button');button.type='button';
      button.className='lind-training-interaction';button.dataset.interactionId=object.id;
      button.setAttribute('aria-label',object.label+'を調べる');
      Object.assign(button.style,{left:object.x-8+'px',top:object.y-8+'px',
        width:object.width+16+'px',height:object.height+16+'px',zIndex:String(Math.round(object.y+object.height+1))});
      button.addEventListener('pointerdown',e=>e.stopPropagation());
      button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();interact(object.id)});
      parent.append(button);
    });
  }
  function nearby() {
    const object=window.LindFieldAssets.objects.find(o=>o.interaction &&
      Math.hypot(px+17-o.x-o.width/2,py+42-o.y-o.height)<=100);
    return object ? interact(object.id) : false;
  }
  function clear() { lastInteraction=null;if(notice)notice.hidden=true; }
  window.LindFieldTraining=Object.freeze({mount,interact,nearby,clear,get lastInteraction(){return lastInteraction;}});
})();
