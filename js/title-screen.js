// TITLE-01 menu, connected to the safe cold restore boundary. NEW GAME confirmation is a modal dialog (TITLE-05B).
(() => {
 'use strict';
 let root,menu,newButton,continueButton,message,launch,active=false,confirmBox=null,starting=false;
 const query=new URLSearchParams(location.search),skip=query.get('title')==='0'||query.get('legacyVillage')==='1';
 function hide(){active=false;if(root)root.hidden=true;document.documentElement?.classList.remove('title-on');LoadingInput.release('title');}
 function refresh(){
  if(!root)return;
  const loading=['LOADING','NEW_GAME'].includes(SaveContinue.phase);
  const checked=SaveContinue.inspect();
  // While the NEW GAME confirmation is open the two menu buttons are disabled, so pointer, Tab and Enter cannot reach them.
  for(const button of root.querySelectorAll('button'))button.disabled=loading||(Boolean(confirmBox)&&!confirmBox.contains?.(button));
  newButton.disabled=loading||Boolean(confirmBox);continueButton.disabled=loading||!checked.ok||Boolean(confirmBox);
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY));}catch{}
  message.textContent=SaveContinue.error||(hasSave&&!checked.ok?checked.error:checked.ok&&!loading?'冒険の記録があります。':'');
  if(SaveContinue.phase==='READY')hide();
  else if(!loading){root.hidden=false;active=true;document.documentElement?.classList.add('title-on');LoadingInput.lock('title');if(!root.contains?.(document.activeElement)||document.activeElement?.disabled||document.activeElement?.hidden)(confirmBox?confirmBox.querySelector('[data-loading-action]'):continueButton.disabled?newButton:continueButton)?.focus?.({preventScroll:true});}
 }
 function show(){
  if(!root){
   // TITLE-04: approved art as independent layers (background / Aidan / logo). All controls stay real HTML buttons; no text or buttons are baked into images.
   root=document.createElement('section');root.id='title-screen';root.setAttribute('aria-label','タイトル');
   const backdrop=document.createElement('div');backdrop.className='title-layer title-backdrop';backdrop.setAttribute('aria-hidden','true');
   const hero=document.createElement('img');hero.className='title-layer title-hero';hero.src='assets/images/characters/aidan_back_v2.png';hero.alt='';hero.setAttribute('aria-hidden','true');hero.setAttribute('decoding','async');hero.setAttribute('draggable','false');
   const title=document.createElement('h1');title.className='title-logo';
   const logo=document.createElement('img');logo.src='img/title/logo.png';logo.alt='THE WINDBOUND OATH — Mionn na Gaoithe';logo.setAttribute('decoding','async');logo.setAttribute('draggable','false');
   // If the logo image cannot load, the plain-text title remains (layout and buttons are unaffected).
   const fallback=document.createElement('span');fallback.className='title-logo-text';fallback.textContent='THE WINDBOUND OATH';
   logo.onerror=()=>{logo.hidden=true;title.classList.add('title-logo-failed');};
   title.append(logo,fallback);
   menu=document.createElement('div');menu.className='title-menu';
   newButton=document.createElement('button');newButton.textContent='NEW GAME';newButton.setAttribute('data-loading-action','new-game');newButton.onclick=()=>newGame();
   continueButton=document.createElement('button');continueButton.textContent='CONTINUE';continueButton.setAttribute('data-loading-action','continue');continueButton.onclick=()=>SaveContinue.start();
   menu.append(newButton,continueButton);
   message=document.createElement('p');message.className='title-message';message.setAttribute('role','status');root.append(backdrop,hero,title,menu,message);document.body.append(root);
  }
  refresh();newButton.focus?.({preventScroll:true});
 }
 async function newGame(confirmed=false){
  if(!launch)return false;
  if(starting)return false;   // one start per press: repeated taps/Enter cannot launch twice
  // NEW GAME never writes or erases the saved record. With a SAVE, ask in a modal dialog (TITLE-05B), not inside the menu.
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY));}catch{}
  if(!confirmed&&hasSave){openConfirm();return false;}
  closeConfirm(false);starting=true;hide();
  try{return await SaveContinue.newGame(launch);}finally{starting=false;}
 }
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
 window.TitleScreen=Object.freeze({begin(cb){launch=cb;if(skip)return cb();show();},refresh,newGame,dismiss:hide,active:()=>active});
})();
