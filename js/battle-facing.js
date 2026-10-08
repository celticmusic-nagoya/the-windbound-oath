// Only the inner image owns facing. Motion roots, HUDs and PNG bytes are untouched.
(() => {
 const modes=new Set(['NORMAL','PREEMPTIVE','BACK_ATTACK']);let mode='NORMAL';
 // Audited native artwork: enemies look right; Fiona's ordinary poses look left.
 // Frontal prayer/support/terminal illustrations have no directional override.
 const frontal=new Set(['prayer','charge','heal','rune','blessing','ko','victory']);
 function paint(image,actor,state){
  if(!image)return;
  const ally=['aidan','fiona'].includes(actor),neutral=actor==='lou'||frontal.has(state);
  const native=actor==='fiona'?-1:1,desired=ally&&mode!=='BACK_ATTACK'?1:-1;
  image.dataset.facingActor=actor;image.dataset.facingState=state;
  image.style.setProperty('--battle-facing',neutral?1:desired*native);
  image.classList.add('battleFacingImage');
 }
 function refresh(){document.querySelectorAll('.battleFacingImage').forEach(i=>paint(i,i.dataset.facingActor,i.dataset.facingState));}
 function set(value){if(!modes.has(value))return false;mode=value;refresh();return true;}
 window.BattleFacing=Object.freeze({paint,set,refresh,get mode(){return mode}});
})();
