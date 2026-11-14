// TITLE-01 menu, connected to the safe cold restore boundary. NEW GAME confirmation is a modal dialog (TITLE-05B).
(() => {
 'use strict';
 let root,menu,newButton,continueButton,message,launch,active=false,confirmBox=null,slotBox=null,starting=false;
 function validSlots(){try{return window.SaveSlots?.list().filter(x=>x.occupied&&!x.corrupt&&SaveContinue.inspect(SaveSlots.payload(x.slot)).ok)||[]}catch{return []}}
 const query=new URLSearchParams(location.search),skip=query.get('title')==='0'||query.get('legacyVillage')==='1';
 function hide(){active=false;if(root)root.hidden=true;document.documentElement?.classList.remove('title-on');LoadingInput.release('title');}
 function refresh(){
  if(!root)return;
  const loading=['LOADING','NEW_GAME'].includes(SaveContinue.phase);
  const checked=SaveContinue.inspect(),slots=validSlots();
  // While the NEW GAME confirmation is open the two menu buttons are disabled, so pointer, Tab and Enter cannot reach them.
  for(const button of root.querySelectorAll('button'))button.disabled=loading||(Boolean(confirmBox||slotBox)&&!(confirmBox||slotBox).contains?.(button));
  newButton.disabled=loading||Boolean(confirmBox);continueButton.disabled=loading||(!checked.ok&&!slots.length)||Boolean(confirmBox||slotBox);
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY));}catch{}
  message.textContent=SaveContinue.error||(slots.length&&!loading?'冒険の記録が '+slots.length+' スロットあります。':hasSave&&!checked.ok?checked.error:checked.ok&&!loading?'冒険の記録があります。':'');
  if(SaveContinue.phase==='READY')hide();
  else if(!loading){root.hidden=false;active=true;document.documentElement?.classList.add('title-on');LoadingInput.lock('title');if(!root.contains?.(document.activeElement)||document.activeElement?.disabled||document.activeElement?.hidden)((confirmBox||slotBox)?(confirmBox||slotBox).querySelector('button:not(:disabled)'):continueButton.disabled?newButton:continueButton)?.focus?.({preventScroll:true});}
 }
 function show(){
  if(!root){
   // TITLE-04: approved art as independent layers (background / Aidan / logo). All controls stay real HTML buttons; no text or buttons are baked into images.
   root=document.createElement('section');root.id='title-screen';root.setAttribute('aria-label','タイトル');
   const backdrop=document.createElement('div');backdrop.className='title-layer title-backdrop';backdrop.setAttribute('aria-hidden','true');
   const hero=document.createElement('img');hero.className='title-layer title-hero';hero.src='assets/images/characters/aidan_back_v2.png';hero.alt='';hero.setAttribute('aria-hidden','true');hero.setAttribute('decoding','async');hero.setAttribute('draggable','false');
   const foreground=document.createElement('div');foreground.className='title-layer title-foreground';foreground.setAttribute('aria-hidden','true');
   const title=document.createElement('h1');title.className='title-logo';
   const logo=document.createElement('img');logo.src='img/title/logo.png';logo.alt='THE WINDBOUND OATH — Mionn na Gaoithe';logo.setAttribute('decoding','async');logo.setAttribute('draggable','false');
   // If the logo image cannot load, the plain-text title remains (layout and buttons are unaffected).
   const fallback=document.createElement('span');fallback.className='title-logo-text';fallback.textContent='THE WINDBOUND OATH';
   logo.onerror=()=>{logo.hidden=true;title.classList.add('title-logo-failed');};
   title.append(logo,fallback);
   menu=document.createElement('div');menu.className='title-menu';
   newButton=document.createElement('button');newButton.textContent='NEW GAME';newButton.setAttribute('data-loading-action','new-game');newButton.onclick=()=>newGame();
   continueButton=document.createElement('button');continueButton.textContent='CONTINUE';continueButton.setAttribute('data-loading-action','continue');continueButton.onclick=()=>openSlotSelector();
   menu.append(newButton,continueButton);
   message=document.createElement('p');message.className='title-message';message.setAttribute('role','status');root.append(backdrop,hero,foreground,title,menu,message);document.body.append(root);
  }
  refresh();newButton.focus?.({preventScroll:true});
 }
 async function newGame(confirmed=false){
  if(!launch)return false;
  if(starting)return false;   // one start per press: repeated taps/Enter cannot launch twice
  // NEW GAME never writes or erases the saved record. With a SAVE, ask in a modal dialog (TITLE-05B), not inside the menu.
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY))||validSlots().length>0}catch{}
  if(!confirmed&&hasSave){openConfirm();return false;}
  closeConfirm(false);starting=true;hide();
  try{return await SaveContinue.newGame(launch);}finally{starting=false;}
 }
 function openSlotSelector(){
  if(slotBox||confirmBox||starting)return;
  slotBox=document.createElement('div');slotBox.className='title-confirm title-slot-picker';slotBox.setAttribute('role','dialog');slotBox.setAttribute('aria-modal','true');slotBox.setAttribute('aria-label','ロードするセーブスロット');
  const label=document.createElement('p');label.textContent='再開する記録を選択してください。';slotBox.append(label);
  const grid=document.createElement('div');grid.className='title-slot-list';
  for(const info of validSlots()){
   const button=document.createElement('button');button.type='button';button.textContent='SLOT '+String(info.slot).padStart(2,'0')+' — 進行 '+info.storyStage+' / '+new Date(info.savedAt).toLocaleString('ja-JP');
   button.onclick=()=>{const raw=SaveSlots.payload(info.slot);closeSlotSelector();void SaveContinue.start(raw)};grid.append(button)
  }
  if(SaveContinue.inspect().ok){const legacy=document.createElement('button');legacy.type='button';legacy.textContent='旧セーブから再開';legacy.onclick=()=>{closeSlotSelector();void SaveContinue.start()};grid.append(legacy)}
  slotBox.append(grid);const cancel=document.createElement('button');cancel.type='button';cancel.textContent='キャンセル';cancel.onclick=()=>closeSlotSelector();slotBox.append(cancel);root.append(slotBox);menu.setAttribute('aria-hidden','true');refresh();cancel.focus?.({preventScroll:true});
 }
 function closeSlotSelector(){if(!slotBox)return;slotBox.remove();slotBox=null;menu.removeAttribute('aria-hidden');refresh();continueButton.focus?.({preventScroll:true})}
 function openConfirm(){
  if(confirmBox)return;
  confirmBox=document.createElement('div');confirmBox.className='title-confirm';confirmBox.setAttribute('role','alertdialog');confirmBox.setAttribute('aria-modal','true');
  confirmBox.setAttribute('aria-labelledby','title-confirm-text');
  const text=document.createElement('p');text.id='title-confirm-text';text.textContent='新しく始めますか？ セーブデータは削除されません。';
  const actions=document.createElement('div');actions.className='title-confirm-actions';
  const yes=document.createElement('button'),no=document.createElement('button');
  yes.textContent='はじめる';yes.setAttribute('data-confirm-new','');yes.setAttribute('data-loading-action','confirm-new');
  no.textContent='キャンセル';no.setAttribute('data-loading-action','cancel-new');
  yes.onclick=()=>{if(yes.disabled)return false;yes.disabled=true;no.disabled=true;return newGame(true);};
  no.onclick=()=>{closeConfirm(true);return false;};
  actions.append(yes,no);confirmBox.append(text,actions);root.append(confirmBox);
  menu.setAttribute('aria-hidden','true');refresh();no.focus?.({preventScroll:true});
 }
 function closeConfirm(restoreFocus){
  if(!confirmBox)return;
  confirmBox.remove();confirmBox=null;menu.removeAttribute('aria-hidden');refresh();
  if(restoreFocus&&!newButton.disabled)newButton.focus?.({preventScroll:true});
 }
 // Full reload is required to discard battle timers and active gameplay state.
 // This does not alter either the numbered slots or the legacy save key.
 function returnToTitle(){
  try{
   const target=new URL(window.location.href);
   target.searchParams.delete('title');target.searchParams.delete('legacyVillage');target.hash='';
   window.location.assign(target.href);return true;
  }catch(_){return false}
 }
 window.TitleScreen=Object.freeze({begin(cb){launch=cb;if(skip)return cb();show();},refresh,newGame,dismiss:hide,returnToTitle,active:()=>active});
})();
