// TITLE-01 menu/NEW GAME confirmation pattern, connected to the safe cold restore boundary.
(() => {
 'use strict';
 let root,newButton,continueButton,message,launch,active=false;
 const query=new URLSearchParams(location.search),skip=query.get('title')==='0'||query.get('legacyVillage')==='1';
 function hide(){active=false;if(root)root.hidden=true;document.documentElement?.classList.remove('title-on');LoadingInput.release('title');}
 function refresh(){
  if(!root)return;
  const loading=['LOADING','NEW_GAME'].includes(SaveContinue.phase);
  const checked=SaveContinue.inspect();
  for(const button of root.querySelectorAll('button'))button.disabled=loading;
  continueButton.disabled=loading||!checked.ok;
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY));}catch{}
  message.textContent=SaveContinue.error||(hasSave&&!checked.ok?checked.error:!continueButton.disabled?'冒険の記録があります。':'');
  if(SaveContinue.phase==='READY')hide();
  else if(!loading){root.hidden=false;active=true;document.documentElement?.classList.add('title-on');LoadingInput.lock('title');if(!root.contains?.(document.activeElement)||document.activeElement?.disabled||document.activeElement?.hidden)(continueButton.disabled?newButton:continueButton).focus?.({preventScroll:true});}
 }
 function show(){
  if(!root){
   root=document.createElement('section');root.id='title-screen';root.setAttribute('aria-label','タイトル');
   const title=document.createElement('h1');title.textContent='THE WINDBOUND OATH';const subtitle=document.createElement('p');subtitle.textContent='Mionn na Gaoithe';
   newButton=document.createElement('button');newButton.textContent='NEW GAME';newButton.setAttribute('data-loading-action','new-game');newButton.onclick=()=>newGame();
   continueButton=document.createElement('button');continueButton.textContent='CONTINUE';continueButton.setAttribute('data-loading-action','continue');continueButton.onclick=()=>SaveContinue.start();
   message=document.createElement('p');message.setAttribute('role','status');root.append(title,subtitle,newButton,continueButton,message);document.body.append(root);
  }
  refresh();newButton.focus?.({preventScroll:true});
 }
 async function newGame(confirmed=false){
  if(!launch)return false;
  // Existing TITLE-01 confirmation: NEW GAME never writes or erases the saved record.
  let hasSave=false;try{hasSave=Boolean(localStorage.getItem(SAVE_KEY));}catch{}
  if(!confirmed&&hasSave){
   message.textContent='新しく始めますか？ セーブデータは削除されません。';
   if(!root.querySelector('[data-confirm-new]')){
    const yes=document.createElement('button'),no=document.createElement('button');yes.textContent='はじめる';no.textContent='戻る';yes.setAttribute('data-confirm-new','');yes.setAttribute('data-loading-action','confirm-new');no.setAttribute('data-loading-action','cancel-new');
    yes.onclick=()=>{yes.remove();no.remove();newGame(true)};no.onclick=()=>{yes.remove();no.remove();refresh()};root.append(yes,no);no.focus?.({preventScroll:true});
   }
   return false;
  }
  hide();return SaveContinue.newGame(launch);
 }
 window.TitleScreen=Object.freeze({begin(cb){launch=cb;if(skip)return cb();show();},refresh,newGame,dismiss:hide,active:()=>active});
})();
